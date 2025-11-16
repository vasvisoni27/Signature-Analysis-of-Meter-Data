A Python tool that loads multiple Excel files of energy meter data, compares consumption patterns across dates and meters, detects deviations, and generates a consolidated Excel report with visual graphs.

📌 Features

Read & merge multiple Excel files

Timestamp preprocessing with timezone conversion (UTC → Asia/Kolkata)

Time-slot alignment for accurate comparison

Meter-wise deviation calculation with remarks

Pairwise deviation analysis per date

Auto-generated Excel report stored in Downloads/deviation_reports/

Single comparison graph for all meters and dates

📂 Output

deviation_report_all_dates.xlsx containing:

{Date}_Pairwise deviation sheet

{Date}_Remarks sheet

Matplotlib plot showing consumption curves for all dates

🛠️ Tech Used

Python, Pandas, Matplotlib, NumPy, OpenPyXL

▶️ Usage

Run the script

Enter Excel file paths separated by comma

View the generated deviation report and graph
