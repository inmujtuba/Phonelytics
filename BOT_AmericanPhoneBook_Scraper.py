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

    def scrape_phone_info(self, driver, number):
        try:
            print(f"Navigating to americaphonebook.com/reverse.php for {number}")
            driver.get("https://www.americaphonebook.com/reverse.php")
            time.sleep(random.uniform(4, 6))

            wait = WebDriverWait(driver, 30)
            print(f"Waiting for page to be ready for {number}")
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            
            print(f"Locating search box for {number}")
            search_box = wait.until(EC.presence_of_element_located((By.NAME, "number")))

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

            print(f"Submitting search for {number}")
            search_box.send_keys(Keys.RETURN)
            time.sleep(random.uniform(5, 7))

            print(f"Waiting for results for {number}")
            wait.until(lambda d: "Here are your" in d.page_source or "searchform2" in d.page_source)
            time.sleep(random.uniform(3, 5))

            print(f"Scraping data from results page for {number}")
            with open(f"debug_{number}_postwait.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"Post-wait debug saved to debug_{number}_postwait.html")

            if "Here are your" not in driver.page_source:
                print(f"No results found for {number}")
                return None

            rows = driver.find_elements(By.XPATH, "//table//tr[td]")
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) < 3:
                    continue
                phone = cells[3].text.strip()
                if phone == number:  # First match with this number
                    name = cells[1].text.strip()
                    full_address = cells[2].text.strip()
                    # Parse "1607 KORNEGAY AVE, WILMINGTON, NC. 28405"
                    parts = [p.strip() for p in full_address.split(",")]
                    address = parts[0]
                    city = parts[1]
                    state_zip = parts[2].split()
                    state = state_zip[0].replace(".", "")
                    zip_code = state_zip[1]

                    print(f"Success for {number}: {name}")
                    return {
                        "Name": name,
                        "Phone number": number,
                        "Address": address,
                        "City": city,
                        "State": state,
                        "Zip Code": zip_code,
                        "Country": "United States"
                    }
            print(f"No matching result found for {number}")
            return None

        except Exception as e:
            print(f"Error scraping {number}: {str(e)}")
            with open(f"debug_{number}_error.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"Error debug saved to debug_{number}_error.html")
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
        self.download_button["state"] = "disabled"
        
        Thread(target=self.process_numbers).start()

    def process_numbers(self):
        total_numbers = len(self.numbers)
        driver = self.setup_driver()
        
        for i, number in enumerate(self.numbers):
            if number:
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
            
        self.start_button["state"] = "normal"
        self.download_button["state"] = "normal" if self.results else "disabled"
        self.status_label["text"] = "Scraping complete - Click 'Download Excel Sheet' to save results"

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