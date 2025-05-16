# Phonelytics
Smart phone number lookup automation tool that scrapes personal details from AmericanPhoneBook.com using a browser-controlled bot.


Phonelytics is an intelligent Python-based scraping application designed to automate the lookup of U.S.-based phone numbers through the website AmericanPhoneBook.com. Built for research, verification, and lead enhancement, this tool enables users to validate and enrich phone number data by retrieving associated personal details such as full name, address, age, and more.

The application offers flexibility in data input — users can either paste phone numbers directly into the app’s textbox or upload a .txt or .xlsx file containing a list of phone numbers. Once the input is provided, Phonelytics initiates a headless browsing session through Mozilla Firefox and starts processing the numbers one by one. For each number, it navigates to AmericanPhoneBook.com, enters the number into the lookup bar, and extracts the available public data including name, street address, city, state, ZIP code, phone number, date of birth, and age. If a number yields no results, it is automatically filtered out from the final list.

Upon completion, Phonelytics generates a structured Excel report consisting only of the successful results, making it a powerful and time-saving tool for call centers, researchers, and professionals dealing with large-scale number validation. This tool is ideal for verifying leads or enriching client databases with publicly available data.

Phonelytics is distributed under the MIT License. It is intended for legal and ethical use only — users must comply with data privacy laws applicable in their region. For feature requests, issues, or collaboration inquiries, please contact jerryparker0710@gmail.com.
