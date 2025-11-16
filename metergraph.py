import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# ---------- 1) Read multiple Excel files ----------
file_paths = input("Enter Excel file paths (separated by comma): ").split(",")
dfs = []
for p in file_paths:
    p = p.strip().strip('"').strip("'")
    if p:
        dfs.append(pd.read_excel(rf"{p}"))

if not dfs:
    raise SystemExit("No valid file paths were provided.")

df = pd.concat(dfs, ignore_index=True)

# ---------- 2) Preprocess ----------
df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
df = df.dropna(subset=['datetime']).copy()
df['datetime'] = df['datetime'].dt.tz_localize("UTC").dt.tz_convert("Asia/Kolkata")

df['Date'] = df['datetime'].dt.date
df['TimeSlot'] = df['datetime'].dt.strftime("%H:%M")

# Create output folder in Downloads
downloads = os.path.join(os.path.expanduser("~"), "Downloads")
output_folder = os.path.join(downloads, "deviation_reports")
os.makedirs(output_folder, exist_ok=True)

# Prepare single Excel file for ALL dates
out_file = os.path.join(output_folder, "deviation_report_all_dates.xlsx")
writer = pd.ExcelWriter(out_file, engine="openpyxl")

# ---------- 3) Build global TimeSlot order ----------
all_slots = sorted(df['TimeSlot'].unique(), key=lambda s: pd.to_datetime(s, format="%H:%M"))
slot_to_idx = {s: i for i, s in enumerate(all_slots)}

# ---------- 4) Plot all dates on same graph ----------
fig, ax = plt.subplots(figsize=(16, 8))

color_cycle = plt.cm.tab10.colors
markers = ['o', 's', 'D', '^', 'v', 'P', '*', 'X']
linestyles = ['-', '--', '-.', ':']

# For each date separately
for d_i, (date, date_group) in enumerate(df.groupby('Date')):
    date_group = date_group.sort_values('datetime')

    mean_lines = {}
    ref_pattern = None
    remarks = []
    style_count = 0

    for meter_id, g in date_group.groupby("MeterId"):
        # Convert TimeSlot → X index
        x_idx = g['TimeSlot'].map(slot_to_idx).to_numpy(dtype=float)

        # Apply small random jitter horizontally & vertically to reduce overlap
        jitter_x = np.random.uniform(-0.15, 0.15, size=len(x_idx))
        jitter_y = (style_count % 5) * 0.05

        ax.plot(
            x_idx + jitter_x, g['kWh'] + jitter_y,
            marker=markers[style_count % len(markers)],
            markersize=5,                  # smaller markers
            alpha=0.8,                     # transparency to see overlaps
            linestyle=linestyles[style_count % len(linestyles)],
            linewidth=1.8,
            color=color_cycle[(style_count + d_i) % len(color_cycle)],
            label=f"Meter {meter_id} | {date}"
        )

        m = g['kWh'].mean()
        mean_lines[meter_id] = m

        # ---------- FIX: unique TimeSlot aggregation ----------
        if ref_pattern is None:
            ref_pattern = (
                g[['TimeSlot', 'kWh']]
                .groupby('TimeSlot')
                .mean()
            )
            ref_meter = meter_id

        g_agg = (
            g[['TimeSlot', 'kWh']]
            .groupby('TimeSlot')
            .mean()
        )

        g_ref = ref_pattern.reindex(g_agg.index).ffill().bfill()

        deviation_series = abs(g_agg['kWh'].to_numpy() - g_ref['kWh'].to_numpy())
        avg_dev = deviation_series.mean()
        dev_pct = (avg_dev / g_ref['kWh'].mean()) * 100 if g_ref['kWh'].mean() != 0 else 0

        if dev_pct <= 5:
            remark = "OK (within ±5%)"
        elif dev_pct <= 10:
            remark = "Moderate deviation (5–10%)"
        else:
            remark = "High deviation (>10%)"

        remarks.append([meter_id, avg_dev, dev_pct, remark])
        style_count += 1

    # ---------- 5) Pairwise deviations ----------
    dev_rows = []
    total_dev_kwh = 0.0
    total_dev_pct = 0.0
    pairs = 0

    meters = sorted(mean_lines.keys())
    for i in range(len(meters)):
        for j in range(i+1, len(meters)):
            a, b = meters[i], meters[j]
            dev = abs(mean_lines[a] - mean_lines[b])
            avg = (mean_lines[a] + mean_lines[b]) / 2.0
            dev_pct = (dev / avg) * 100 if avg != 0 else 0.0

            dev_rows.append([f"{a} vs {b}", dev, dev_pct])
            total_dev_kwh += dev
            total_dev_pct += dev_pct
            pairs += 1

    if pairs > 0:
        total_dev_pct /= pairs
        dev_rows.append(["TOTAL", total_dev_kwh, total_dev_pct])

    dev_df = pd.DataFrame(dev_rows, columns=["Meters", "Deviation (kWh)", "Deviation (%)"])
    remark_df = pd.DataFrame(remarks, columns=["MeterId", "Avg Deviation (kWh)", "Deviation (%)", "Remark"])

    dev_df.to_excel(writer, sheet_name=f"{date}_Pairwise", index=False)
    remark_df.to_excel(writer, sheet_name=f"{date}_Remarks", index=False)

# Save Excel file finally
writer.close()
print(f"✅ Single Excel report saved: {out_file}")

# --------- 6) Styling for plot ---------
ax.set_title("Consumption Comparison (All Dates)", fontsize=16, fontweight="bold")
ax.set_xlabel("Time Slots (Asia/Kolkata)", fontsize=12)
ax.set_ylabel("kWh Consumption", fontsize=12)

ax.set_xticks(range(len(all_slots)))
ax.set_xticklabels(all_slots, rotation=90, fontsize=8)

ax.grid(True, linestyle="--", alpha=0.4)
ax.legend(fontsize=7, loc="upper right", framealpha=0.9, ncol=3)  # compact legend

plt.tight_layout()
plt.show()
