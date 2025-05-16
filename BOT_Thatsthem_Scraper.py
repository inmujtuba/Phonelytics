import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import re
import time
import random
import os
from threading import Thread
import requests
from selenium.common.exceptions import TimeoutException, WebDriverException

class PhoneScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Phone Number Scraper")
        self.root.geometry("800x500")
        self.root.configure(bg="#2c3e50")
        
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Helvetica", 10), padding=5)
        self.style.configure("TLabel", font=("Helvetica", 11), background="#2c3e50", foreground="white")
        
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill="both", expand=True)
        
        self.input_label = ttk.Label(self.main_frame, text="Enter Numbers or Load File:")
        self.input_label.grid(row=0, column=0, pady=5, sticky="w")
        
        self.input_text = tk.Text(self.main_frame, height=15, width=50, bg="#34495e", fg="white")
        self.input_text.grid(row=1, column=0, padx=5, pady=5)
        
        self.load_button = ttk.Button(self.main_frame, text="Load File", command=self.load_file)
        self.load_button.grid(row=2, column=0, pady=5)
        
        self.start_button = ttk.Button(self.main_frame, text="Start Scraping", command=self.start_scraping)
        self.start_button.grid(row=3, column=0, pady=5)
        
        self.stop_button = ttk.Button(self.main_frame, text="Stop Scraping", command=self.stop_scraping, state="disabled")
        self.stop_button.grid(row=3, column=1, pady=5)
        
        self.progress_label = ttk.Label(self.main_frame, text="Progress:")
        self.progress_label.grid(row=4, column=0, pady=5, sticky="w")
        
        self.progress_bar = ttk.Progressbar(self.main_frame, length=300, mode="determinate")
        self.progress_bar.grid(row=5, column=0, pady=5)
        
        self.status_label = ttk.Label(self.main_frame, text="")
        self.status_label.grid(row=6, column=0, pady=5)
        
        self.download_button = ttk.Button(self.main_frame, text="Download Excel Sheet", command=self.save_results, state="disabled")
        self.download_button.grid(row=7, column=0, pady=5)
        
        self.results = []
        self.numbers = []
        self.driver = None
        self.is_scraping = False
        self.is_paused = False
        self.human_verification_popup = None

    def format_phone_number(self, number):
        cleaned = re.sub(r'[^\d+]', '', str(number).strip())
        if len(cleaned) == 10 and cleaned.isdigit():
            return cleaned
        if cleaned.startswith('+1') and len(cleaned) == 12:
            return cleaned[2:]
        elif cleaned.startswith('1') and len(cleaned) == 11:
            return cleaned[1:]
        return None

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("Excel files", "*.xlsx")])
        if file_path:
            self.input_text.delete(1.0, tk.END)
            try:
                if file_path.endswith('.txt'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.input_text.insert(tk.END, f.read())
                elif file_path.endswith('.xlsx'):
                    df = pd.read_excel(file_path)
                    numbers = '\n'.join(df.iloc[:, 0].astype(str))
                    self.input_text.insert(tk.END, numbers)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {str(e)}")

    def setup_driver(self):
        if not self.driver:
            print("Initializing Firefox driver...")
            firefox_options = Options()
            firefox_options.add_argument("--disable-blink-features=AutomationControlled")
            firefox_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0")
            firefox_options.add_argument("--disable-extensions")
            try:
                self.driver = webdriver.Firefox(options=firefox_options)
                self.driver.set_window_size(1200, 800)
                self.driver.set_window_position(100, 100)
                print("Driver initialized successfully.")
            except Exception as e:
                print(f"Failed to initialize driver: {str(e)}")
                raise
        return self.driver

    def check_internet(self):
        try:
            requests.get("https://www.google.com", timeout=5)
            return True
        except requests.ConnectionError:
            return False

    def check_human_verification(self, driver):
        try:
            # Check for common verification elements or text
            verification_indicators = [
                "verify you are not a robot",
                "prove you are human",
                "sign up to continue",
                "captcha",
                "recaptcha"
            ]
            page_source = driver.page_source.lower()
            for indicator in verification_indicators:
                if indicator in page_source:
                    return True
            # Check for specific elements that might indicate a verification page
            if driver.find_elements(By.ID, "recaptcha") or driver.find_elements(By.CLASS_NAME, "g-recaptcha"):
                return True
            return False
        except:
            return False

    def show_human_verification_popup(self):
        if not self.human_verification_popup:
            self.human_verification_popup = tk.Toplevel(self.root)
            self.human_verification_popup.title("Human Verification Required")
            self.human_verification_popup.geometry("400x200")
            self.human_verification_popup.configure(bg="#2c3e50")
            self.human_verification_popup.transient(self.root)
            self.human_verification_popup.grab_set()

            ttk.Label(self.human_verification_popup, text="The website requires human verification or signup.\nPlease complete the verification in the browser,\nthen click 'Done' to resume.", font=("Helvetica", 11), background="#2c3e50", foreground="white").pack(pady=20)
            ttk.Button(self.human_verification_popup, text="Done", command=self.resume_after_verification).pack(pady=10)

            self.is_paused = True
            self.status_label["text"] = "Paused: Waiting for human verification"
            self.root.update()

    def resume_after_verification(self):
        if self.human_verification_popup:
            self.human_verification_popup.destroy()
            self.human_verification_popup = None
        self.is_paused = False
        self.status_label["text"] = "Resuming scraping..."
        self.root.update()

    def scrape_phone_info(self, driver, number):
        try:
            print(f"Navigating to thatsthem.com/reverse-phone-lookup for {number}")
            driver.get("https://thatsthem.com/reverse-phone-lookup")
            time.sleep(random.uniform(4, 6))

            wait = WebDriverWait(driver, 30)
            print(f"Waiting for page to be ready for {number}")
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            
            # Check for human verification
            if self.check_human_verification(driver):
                print(f"Human verification detected for {number}")
                self.root.after(0, self.show_human_verification_popup)
                while self.is_paused and self.is_scraping:
                    time.sleep(1)
                if not self.is_scraping:
                    return None

            print(f"Locating search box for {number}")
            try:
                search_box = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "form-control")))
            except:
                print(f"Class 'form-control' not found, trying fallback locator for {number}")
                search_box = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='text']")))

            print(f"Clicking search box for {number}")
            driver.execute_script("arguments[0].click();", search_box)
            time.sleep(random.uniform(0.5, 1))

            print(f"Clearing search box for {number}")
            search_box.clear()
            time.sleep(random.uniform(0.5, 1))

            print(f"Typing {number}")
            for digit in number:
                search_box.send_keys(digit)
                time.sleep(random.uniform(0.2, 0.4))
            time.sleep(random.uniform(0.5, 1))

            original_window = driver.current_window_handle
            print(f"Original window handle: {original_window}")

            print(f"Submitting search for {number}")
            search_box.send_keys(Keys.RETURN)
            time.sleep(random.uniform(5, 7))

            print(f"Switching to new tab for {number}")
            wait.until(EC.number_of_windows_to_be(2))
            for window_handle in driver.window_handles:
                if window_handle != original_window:
                    driver.switch_to.window(window_handle)
                    break
            print(f"Switched to new window handle: {driver.current_window_handle}")

            print(f"Waiting for results or no-results message for {number}")
            wait.until(lambda d: d.find_elements(By.CLASS_NAME, "record") or 
                        "no results found" in d.page_source.lower())
            time.sleep(random.uniform(3, 5))

            # Check for human verification again on results page
            if self.check_human_verification(driver):
                print(f"Human verification detected on results page for {number}")
                self.root.after(0, self.show_human_verification_popup)
                while self.is_paused and self.is_scraping:
                    time.sleep(1)
                if not self.is_scraping:
                    driver.close()
                    driver.switch_to.window(original_window)
                    return None

            print(f"Scraping data from results page for {number}")
            if "no results found" in driver.page_source.lower():
                print(f"No results found for {number}")
                driver.close()
                driver.switch_to.window(original_window)
                return None

            record = driver.find_element(By.CLASS_NAME, "record")
            name = record.find_element(By.CLASS_NAME, "name").text.strip() if record.find_elements(By.CLASS_NAME, "name") else ""
            if not name:
                print(f"No name found for {number}")
                driver.close()
                driver.switch_to.window(original_window)
                return None

            location = record.find_element(By.CLASS_NAME, "location") if record.find_elements(By.CLASS_NAME, "location") else None
            street = location.find_element(By.CLASS_NAME, "street").text.strip() if location and location.find_elements(By.CLASS_NAME, "street") else ""
            city = location.find_element(By.CLASS_NAME, "city").text.strip() if location and location.find_elements(By.CLASS_NAME, "city") else ""
            state = location.find_element(By.CLASS_NAME, "state").text.strip() if location and location.find_elements(By.CLASS_NAME, "state") else ""
            zip_code = location.find_element(By.CLASS_NAME, "zip").text.strip().split('+')[0] if location and location.find_elements(By.CLASS_NAME, "zip") else ""
            age_text = record.find_element(By.CLASS_NAME, "age").text.strip() if record.find_elements(By.CLASS_NAME, "age") else ""

            # Parse age and DOB
            dob = ""
            age = ""
            if age_text:
                match = re.search(r"Born (.*?)\((\d+) years old\)", age_text)
                if match:
                    dob = match.group(1).strip()
                    age = match.group(2).strip()

            print(f"Success for {number}: {name}")
            driver.close()
            driver.switch_to.window(original_window)
            return {
                "Name": name,
                "Phone number": number,
                "Address": street,
                "City": city,
                "State": state,
                "Zip Code": zip_code,
                "Country": "United States",
                "Date of Birth": dob,
                "Age": age
            }
        except (TimeoutException, WebDriverException) as e:
            print(f"Network or driver error for {number}: {str(e)}")
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(original_window)
            return None

    def start_scraping(self):
        self.results = []
        input_text = self.input_text.get(1.0, tk.END).strip()
        self.numbers = [self.format_phone_number(n) for n in input_text.split('\n') if self.format_phone_number(n)]
        
        if not self.numbers:
            messagebox.showerror("Error", "No valid phone numbers detected!")
            return
            
        if len(self.numbers) > 100000:
            messagebox.showerror("Error", "Maximum 100,000 numbers allowed!")
            return
            
        self.progress_bar["maximum"] = len(self.numbers)
        self.start_button["state"] = "disabled"
        self.stop_button["state"] = "normal"
        self.download_button["state"] = "disabled"
        self.is_scraping = True
        
        Thread(target=self.process_numbers).start()

    def stop_scraping(self):
        self.is_scraping = False
        self.stop_button["state"] = "disabled"
        self.start_button["state"] = "normal"
        self.download_button["state"] = "normal" if self.results else "disabled"
        self.status_label["text"] = f"Scraping stopped - {len(self.results)} numbers processed. Click 'Download Excel Sheet' to save results."
        self.numbers = []  # Clear remaining numbers
        self.input_text.delete(1.0, tk.END)  # Clear input text
        self.progress_bar["value"] = 0
        self.root.update()

    def process_numbers(self):
        total_numbers = len(self.numbers)
        driver = self.setup_driver()
        
        for i, number in enumerate(self.numbers[:]):  # Use slice to allow modification
            if not self.is_scraping:
                break
                
            # Check internet connection
            while not self.check_internet() and self.is_scraping:
                self.is_paused = True
                self.status_label["text"] = "Paused: No internet connection. Waiting to reconnect..."
                self.root.update()
                time.sleep(5)
            if not self.is_scraping:
                break
                
            self.is_paused = False
            result = self.scrape_phone_info(driver, number)
            if result:
                self.results.append(result)
                
            self.progress_bar["value"] = i + 1
            self.status_label["text"] = f"Processed: {i + 1}/{total_numbers} | Found: {len(self.results)}"
            self.root.update()
            time.sleep(random.uniform(2, 4))
        
        try:
            driver.quit()
            self.driver = None
        except:
            pass
            
        if self.is_scraping:  # Only update UI if not stopped manually
            self.start_button["state"] = "normal"
            self.stop_button["state"] = "disabled"
            self.download_button["state"] = "normal" if self.results else "disabled"
            self.status_label["text"] = "Scraping complete - Click 'Download Excel Sheet' to save results"
        self.is_scraping = False
        self.root.update()

    def save_results(self):
        if not self.results:
            messagebox.showwarning("Warning", "No data found to save!")
            return
            
        df = pd.DataFrame(self.results)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        default_filename = f"phone_search_results_{timestamp}.xlsx"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile=default_filename,
            filetypes=[("Excel files", "*.xlsx")])
            
        if file_path:
            try:
                df.to_excel(file_path, index=False)
                self.status_label["text"] = f"Results saved to {os.path.basename(file_path)}"
                messagebox.showinfo("Success", f"Results saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PhoneScraperApp(root)
    root.mainloop()