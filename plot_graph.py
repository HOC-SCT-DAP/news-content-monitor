import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def generate_github_visuals(file_path):
    # Load data
    df = pd.read_csv(file_path)
    df['Date Published'] = pd.to_datetime(df['Date Published'])

    # --- Chart 1: Average Heading Length by Committee ---
    plt.figure(figsize=(10, 6))
    cttee_data = df.groupby('Committee Name')['Heading Word Count'].mean().sort_values()
    
    cttee_data.plot(kind='barh', color='#2ea44f', edgecolor='#1b1f23') # GitHub-style green
    plt.title('Average Heading Word Count by Committee', fontweight='bold')
    plt.xlabel('Average Words')
    plt.ylabel('')
    plt.tight_layout()
    
    plt.savefig('docs/committee_avg.svg') 
    plt.close()

    # --- Chart 2: Monthly Heading Trend ---
    plt.figure(figsize=(10, 6))
    # 'ME' is Month End frequency
    monthly_data = df.resample('ME', on='Date Published')['Heading Word Count'].mean()
    
    plt.bar(monthly_data.index, monthly_data.values, width=20, color='#0969da', edgecolor='#1b1f23') # GitHub-style blue
    plt.title('Monthly Average Heading Word Count', fontweight='bold')
    
    # Format the X-axis for dates
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45)
    
    plt.ylabel('Average Words')
    plt.tight_layout()

    plt.savefig('docs/monthly_trend.svg')
    plt.close()

    print("Success! Generated SVG (for GitHub/HTML) and PDF (for reports).")

if __name__ == "__main__":
    generate_github_visuals('committee_news.csv')