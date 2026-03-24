import pandas as pd
import os

def generate_index_html(csv_path, output_dir='docs'):
    # 1. Create the docs folder if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 2. Load and process the data
    df = pd.read_csv(csv_path)
    df['Date Published'] = pd.to_datetime(df['Date Published'])
    
    # 1. Filter: Keep only rows where 'Heading Word Count' is greater than 10
    filtered_df = df[df['Heading Word Count'] > 10]

    # 2. Sort & Slice: Get the 30 most recent from that filtered set
    recent_df = filtered_df.sort_values(by='Date Published', ascending=False).head(30)  
    
    # Format the date for the table display
    recent_df['Date Published'] = recent_df['Date Published'].dt.strftime('%d %b %Y')

    # 3. Build the HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Committee News Dashboard</title>
        <style>
            body {{ font-family: -apple-system, sans-serif; line-height: 1.6; color: #24292f; max-width: 1000px; margin: 0 auto; padding: 20px; }}
            h1, h2 {{ border-bottom: 1px solid #d0d7de; padding-bottom: 10px; }}
            .visuals {{ display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 40px; }}
            .visuals img {{ border: 1px solid #d0d7de; border-radius: 6px; width: 100%; max-width: 480px; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; font-size: 0.9em; }}
            th {{ background-color: #f6f8fa; text-align: left; padding: 12px; border: 1px solid #d0d7de; }}
            td {{ padding: 12px; border: 1px solid #d0d7de; }}
            tr:nth-child(even) {{ background-color: #f6f8fa; }}
            .download-link {{ display: inline-block; margin-top: 20px; padding: 10px 15px; background: #2ea44f; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; }}
            .download-link:hover {{ background: #2c974b; }}
            .footer {{ margin-top: 50px; font-size: 0.8em; color: #57606a; }}
            .modal {{
            display: none; 
            position: fixed; 
            z-index: 1000; 
            left: 0; top: 0;
            width: 100%; height: 100%;
            background-color: rgba(0,0,0,0.8); /* Black w/ opacity */
            }}
            .modal-content {{
            margin: auto;
            display: block;
            max-width: 90%;
            max-height: 90vh;
            margin-top: 5vh;
            }}
            .close {{
            position: absolute;
            top: 20px; right: 35px;
            color: white; font-size: 40px; font-weight: bold; cursor: pointer;
            }}
        </style>
    </head>
    <body>
        <h1>Committee News Analytics</h1>
        
        <h2>Visual Trends</h2>
        <div class="visuals">
            <a href="https://hoc-sct-dap.github.io/news-content-monitor/monthly_trend.svg"><img src="monthly_trend.svg" alt="Monthly Trend"></a>
            <a href="https://hoc-sct-dap.github.io/news-content-monitor/committee_avg.svg"><img src="committee_avg.svg" alt="Committee Averages"></a>
        </div>

        <h2>Latest 30 headlines with more than 10 words</h2>
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Committee</th>
                    <th>Heading</th>
                    <th>Heading word count</th>
                    <th>Article word count</th>
                    <th>Article readability score</th>
                </tr>
            </thead>
            <tbody>
    """

    # Add the table rows
    for _, row in recent_df.iterrows():
        html_content += f"""
                <tr>
                    <td>{row['Date Published']}</td>
                    <td>{row['Committee Name']}</td>
                    <td>{row['Heading']}</td>
                    <td>{row['Heading Word Count']}</td>
                    <td>{row['Full Text Word Count']}</td>
                    <td>{row['Full Text Readability']}</td>
                </tr>"""

    # Add the closing tags and the download link
    html_content += f"""
            </tbody>
        </table>

        <a href="committee_news.csv" class="download-link">📥 Download Full CSV Data</a>

        <div class="footer">
            <p>Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>
    </body>
    </html>
    """

    # 4. Write the file
    file_path = os.path.join(output_dir, 'index.html')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Dashboard generated in {file_path}")

if __name__ == "__main__":
    generate_index_html('docs/committee_news.csv')
