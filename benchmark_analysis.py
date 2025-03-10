import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib as mpl
import numpy as np

# Configure matplotlib to display Traditional Chinese characters
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
mpl.rcParams['font.family'] = 'sans-serif'

def calculate_percentiles(data, value):
    """
    Calculate the percentage of values lower, equal, and higher than the given value
    Returns None if data is empty or invalid
    """
    if data is None or len(data) == 0:
        return None
    
    total = len(data)
    lower = (data < value).sum() / total * 100
    equal = (data == value).sum() / total * 100
    higher = (data > value).sum() / total * 100
    
    # Ensure percentages add up to exactly 100%
    total_percentage = lower + equal + higher
    if abs(total_percentage - 100) > 0.01:
        lower = (lower / total_percentage) * 100
        equal = (equal / total_percentage) * 100
        higher = (higher / total_percentage) * 100
    
    return lower, equal, higher

# Set page config
st.set_page_config(page_title='Taiwan Petrochemical Industry Emissions Benchmark Analysis', layout='wide')

# Title
st.title('Taiwan Petrochemical Industry Emissions Benchmark Analysis')

# Load and prepare data
st.sidebar.header('Data Upload')

uploaded_file = st.sidebar.file_uploader("Upload ESG Benchmark Analysis File (XLSX)", type=['xlsx'])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        df_emissions_gov = df[(df['子分類']=='溫室氣體排放')&(df['來自公司報告'].isna())]
        
        # Sidebar for controls
        st.sidebar.header('Analysis Parameters')
        
        # Get unique companies and years
        companies = sorted(df_emissions_gov['中文名稱'].unique())
        years = sorted(df_emissions_gov['年份'].unique())
        
        # Create selection widgets
        selected_company = st.sidebar.selectbox(
            'Select Company',
            companies,
            index=companies.index('台塑') if '台塑' in companies else 0
        )
        
        selected_year = st.sidebar.selectbox(
            'Select Year',
            years
        )
        
        # Add time trend analysis tab
        st.sidebar.markdown("---")
        st.sidebar.subheader("Time Trend Analysis")
        show_trend = st.sidebar.checkbox("Show Historical Trend")
        
        # Filter data based on selection
        year_data = df_emissions_gov[
            (df_emissions_gov['項目'] == '直接＋間接排放') & 
            (df_emissions_gov['年份'] == selected_year)
        ]
        
        company_data = year_data[year_data['中文名稱'] == selected_company]
        
        # Main content area - Time Trend Analysis
        if show_trend:
            st.markdown("## Historical Emissions Trend Analysis")
            
            # Get data for all years for the selected company
            company_all_years = df_emissions_gov[
                (df_emissions_gov['項目'] == '直接＋間接排放') & 
                (df_emissions_gov['中文名稱'] == selected_company)
            ]
            
            if not company_all_years.empty and len(company_all_years) > 1:
                # Create trend visualization - INCREASED SIZE
                fig_trend, ax_trend = plt.subplots(figsize=(15, 8))
                
                # Plot the company's trend
                company_trend = company_all_years.sort_values('年份')
                ax_trend.plot(company_trend['年份'], company_trend['數值'], 
                             marker='o', linewidth=3, color='orange', label=selected_company)
                
                # Add industry average for comparison
                industry_avg = df_emissions_gov[
                    (df_emissions_gov['項目'] == '直接＋間接排放')
                ].groupby('年份')['數值'].mean().reset_index()
                
                ax_trend.plot(industry_avg['年份'], industry_avg['數值'], 
                             marker='s', linewidth=3, color='blue', linestyle='--', label='Industry Average')
                
                ax_trend.set_title(f"{selected_company} Historical Emissions Trend", fontsize=16)
                ax_trend.set_xlabel("Year", fontsize=14)
                ax_trend.set_ylabel("Emissions", fontsize=14)
                ax_trend.tick_params(axis='both', which='major', labelsize=12)
                ax_trend.grid(True, linestyle='--', alpha=0.7)
                ax_trend.legend(fontsize=12)
                
                st.pyplot(fig_trend)
                
                # Calculate year-over-year changes
                if len(company_trend) > 1:
                    company_trend['變化率'] = company_trend['數值'].pct_change() * 100
                    
                    st.markdown("### Annual Change Rate")
                    
                    # Create a bar chart of year-over-year changes 
                    fig_change, ax_change = plt.subplots(figsize=(15, 7))
                    
                    years = company_trend['年份'].iloc[1:].astype(str).tolist()
                    changes = company_trend['變化率'].iloc[1:].tolist()
                    
                    bars = ax_change.bar(years, changes, color=['green' if x < 0 else 'red' for x in changes], width=0.6)
                    
                    for bar, change in zip(bars, changes):
                        height = bar.get_height()
                        # Simplified label positioning
                        # Place labels in the middle of each bar with white text
                        label_y_pos = height / 2  # Middle of the bar
                        
                        ax_change.text(bar.get_x() + bar.get_width()/2., label_y_pos,
                                      f'{change:.1f}%', ha='center', va='center', 
                                      fontweight='bold', fontsize=12, color='white')
                    
                    ax_change.axhline(y=0, color='black', linestyle='-', alpha=0.3)
                    ax_change.set_title(f"{selected_company} Annual Emissions Change Rate", fontsize=16)
                    ax_change.set_xlabel("Year", fontsize=14)
                    ax_change.set_ylabel("Change Rate (%)", fontsize=14)
                    ax_change.tick_params(axis='both', which='major', labelsize=12)
                    ax_change.grid(True, axis='y', linestyle='--', alpha=0.7)
                    
                    st.pyplot(fig_change)
                    
                    avg_change = company_trend['變化率'].mean()
                    latest_change = company_trend['變化率'].iloc[-1]
                    
                    st.markdown(f"""
                    ### Trend Analysis
                    
                    - **Average Annual Change Rate**: {avg_change:.1f}% 
                    - **Latest Annual Change Rate**: {latest_change:.1f}%
                    - **Overall Trend**: {'Decreasing ✅' if avg_change < 0 else 'Increasing ⚠️'}
                    """)
            else:
                st.warning(f"Not enough historical data to analyze trends for {selected_company}.")
        
        # Display the main analysis if not showing trend or if showing both
        show_current = not show_trend or (show_trend and st.checkbox("Also Show Current Year Analysis", value=True))
        
        if show_current and not company_data.empty:
            company_value = company_data.iloc[0]['數值']
            
            # Calculate percentiles
            result = calculate_percentiles(year_data['數值'], company_value)
            
            if result is not None:
                lower_emission, equal_emission, higher_emission = result
                
                # First display the visualization at full width
                # Create visualization - INCREASED SIZE
                fig, ax = plt.subplots(figsize=(18, 10))
                sns.kdeplot(data=year_data, x='數值', fill=True, 
                           color="skyblue", alpha=0.5, 
                           label="Industry Distribution", ax=ax)
                
                # Plot line for selected company
                ax.axvline(company_value, color='orange', 
                          linestyle='--', label=selected_company, linewidth=3)
                
                # Calculate y-axis limits for better text positioning
                ymin, ymax = ax.get_ylim()
                text_y = ymax * 0.8
                
                # Add annotations with larger font
                ax.text(company_value, text_y,
                       f'{selected_company} Emissions: {company_value:.1f}\n'
                       f'Lower than {selected_company}: {lower_emission:.1f}%\n'
                       f'Higher than {selected_company}: {higher_emission:.1f}%',
                       color='orange', fontsize=16, fontweight='bold',
                       bbox=dict(facecolor='white', alpha=0.7, 
                                edgecolor='none', pad=1.5),
                       horizontalalignment='left')
                
                ax.set_title(f"Year {selected_year} Emissions Distribution", fontsize=20)
                ax.set_xlabel("Emissions", fontsize=16)
                ax.set_ylabel("Density", fontsize=16)
                ax.tick_params(axis='both', which='major', labelsize=14)
                ax.legend(fontsize=14)
                
                st.pyplot(fig)
                
                # Then display the analysis results with simple text
                st.markdown("### Analysis Results")
                st.markdown(f"**Year {selected_year} {selected_company} Emissions Distribution Position:**")
                
                st.markdown("📊 Distribution Statistics:")
                st.markdown(f"- {lower_emission:.1f}% of companies have lower emissions than {selected_company}")
                st.markdown(f"- {equal_emission:.1f}% of companies have similar emissions to {selected_company}")
                st.markdown(f"- {higher_emission:.1f}% of companies have higher emissions than {selected_company}")
                
                st.markdown(f"📈 {selected_company} Emissions: **{company_value:.1f}**")
            else:
                st.error("Unable to calculate percentiles - invalid data")
        elif show_current:
            st.error(f"No data found for {selected_company} in year {selected_year}")
    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
else:
    st.info("Please upload the ESG Benchmark Analysis Excel file to begin analysis.")
    st.markdown("""
    ### Instructions:
    1. Click the "Browse files" button in the sidebar
    2. Select your ESG Benchmark Analysis Excel file
    3. After uploading, you'll be able to select a company and year for analysis
    """)

# Add custom CSS to improve appearance
st.markdown("""
<style>
    .stApp {
        max-width: 1400px;
        margin: 0 auto;
    }
    h1 {
        color: #2c3e50;
        padding-bottom: 20px;
        border-bottom: 1px solid #eee;
        font-size: 2.5rem;
    }
    h2 {
        color: #3498db;
        margin-top: 30px;
        font-size: 2rem;
    }
    h3 {
        color: #2980b9;
        font-size: 1.5rem;
    }
    .stSidebar .stRadio > label {
        font-weight: bold;
        color: #2c3e50;
    }
    .stSidebar [data-testid="stVerticalBlock"] {
        padding-top: 2rem;
    }
    .stSidebar [data-testid="stMarkdownContainer"] > h3 {
        margin-bottom: 1rem;
    }
    footer {
        visibility: hidden;
    }
    /* Increase text size throughout the app */
    .stMarkdown, p, li {
        font-size: 1.1rem;
    }
    /* Make sidebar text larger */
    .stSidebar [data-testid="stMarkdownContainer"] {
        font-size: 1.2rem;
    }
</style>
""", unsafe_allow_html=True) 