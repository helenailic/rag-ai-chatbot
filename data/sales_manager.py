
import sqlite3
import pandas as pd
import re
from datetime import datetime
from openai import OpenAI
import os
#used to handle sales report function
class SalesManager:
    def __init__(self, db_path='events.db'):
        self.db_path = db_path
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def parse_dates_from_input(self, user_input):  # Added self parameter
        """Parse dates from user input with improved date handling"""
        # Regular expression to find all dates in the format MM/DD/YY or MM/DD/YYYY
        dates = re.findall(r'\b\d{2}/\d{2}/(?:\d{2}|\d{4})\b', user_input)
        if dates:
            try:
                # Try first with 2-digit year format
                parsed_dates = []
                for date in dates:
                    try:
                        # If date has 2-digit year
                        parsed_date = datetime.strptime(date, "%m/%d/%y")
                    except ValueError:
                        # If date has 4-digit year
                        parsed_date = datetime.strptime(date, "%m/%d/%Y")
                    parsed_dates.append(parsed_date)
                
                parsed_dates.sort()
                return parsed_dates
            except ValueError:
                return None
        return None

    @staticmethod  # Made this a static method since it doesn't need self
    def format_currency(value):
        """Format numerical values as currency"""
        return f"${value:,.2f}"
    def debug_date_format(self, user_input):
        """Debug helper to print date formats"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check what format dates are stored in
        cursor.execute('SELECT "Sale Date" FROM events LIMIT 5')
        sample_dates = cursor.fetchall()
        print(f"Sample dates in database: {sample_dates}")
        
        # Check specific date
        target_date = "10/02/24"
        cursor.execute('SELECT COUNT(*) FROM events WHERE "Sale Date" = ?', (target_date,))
        count = cursor.fetchone()[0]
        print(f"Records found for {target_date}: {count}")
        
        conn.close()

    def get_openai_insights(self, report_string):
        """Get AI insights for the sales report"""
        prompt = (
            "Analyze the following sales report and provide 3-5 key insights about "
            "sales performance, focusing on: highest/lowest performing events, "
            "notable patterns, and significant profit/loss items. Be concise and specific.\n\n"
            f"{report_string}\n\n"
        )
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant providing concise sales analytics."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return None

    def generate_report(self, user_input):
        """Generate sales report based on user input"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            parsed_dates = self.parse_dates_from_input(user_input)
            
            if parsed_dates:
                if len(parsed_dates) == 2:
                    # Date range
                    start_date = parsed_dates[0].strftime("%m/%d/%y")
                    end_date = parsed_dates[1].strftime("%m/%d/%y")
                    date_condition = f"""
                    WHERE substr("Sale Date", 1, 8) BETWEEN '{start_date}' AND '{end_date}'
                    """
                    report_title = f"from {start_date} to {end_date}"
                else:
                    # Single date - match first 8 characters (MM/DD/YY)
                    target_date = parsed_dates[0].strftime("%m/%d/%y")
                    date_condition = f"""WHERE substr("Sale Date", 1, 8) = '{target_date}'"""
                    report_title = f"for {target_date}"
            elif "all time" in user_input.lower():
                date_condition = ""
                report_title = "all-time"
            else:
                date_condition = ""
                report_title = "all-time"

            query = f"""
                SELECT 
                    "Event" AS Event,
                    "Event Date" AS "Event Date",
                    SUM("Quantity") AS "Total Quantity",
                    SUM("Gross Sale [$]") AS "Total Sales",
                    SUM("Profit [$]") AS "Total Profit"
                FROM events
                {date_condition}
                GROUP BY "Event", "Event Date"
                ORDER BY "Event Date";
            """

            print(f"Executing query: {query}")
            report_df = pd.read_sql_query(query, conn)
            print(f"Found {len(report_df)} records")

            if report_df.empty:
                return f"No sales data available {report_title}."

            # Format the report
            report_df["Total Sales"] = report_df["Total Sales"].apply(lambda x: f"${x:,.2f}")
            report_df["Total Profit"] = report_df["Total Profit"].apply(lambda x: f"${x:,.2f}")
            
            # Calculate totals
            total_quantity = report_df["Total Quantity"].sum()
            total_sales = report_df["Total Sales"].str.replace('$', '').str.replace(',', '').astype(float).sum()
            total_profit = report_df["Total Profit"].str.replace('$', '').str.replace(',', '').astype(float).sum()

            # Format the output
            output = []
            # Header
            output.append("\n" + "=" * 100)
            output.append(f"SALES REPORT {report_title.upper()}")
            output.append("=" * 100)
            output.append("")
            
            # Column Headers with fixed widths
            output.append(f"{'Event':<50} {'Event Date':<12} {'Quantity':<10} {'Total Sales':<15} {'Total Profit':<15}")
            output.append("-" * 100)
            
            # Format each row
            for _, row in report_df.iterrows():
                output.append(
                    f"{row['Event']:<50} "
                    f"{row['Event Date']:<12} "
                    f"{row['Total Quantity']:<10} "
                    f"{row['Total Sales']:<15} "
                    f"{row['Total Profit']:<15}"
                )
            
            # Summary section
            output.append("\n" + "=" * 100)
            output.append("SUMMARY")
            output.append("-" * 100)
            output.append(f"Total Events:     {len(report_df):>10}")
            output.append(f"Total Quantity:   {total_quantity:>10,}")
            output.append(f"Total Sales:      {self.format_currency(total_sales):>10}")
            output.append(f"Total Profit:     {self.format_currency(total_profit):>10}")
            output.append("=" * 100)
            
            # Get insights from OpenAI
            try:
                insights = self.get_openai_insights("\n".join(output))
                if insights:
                    output.append("\nINSIGHTS")
                    output.append("-" * 100)
                    output.append(insights)
                    output.append("=" * 100)
            except Exception as e:
                print(f"Error getting insights: {str(e)}")

            return "\n".join(output)

        except Exception as e:
            print(f"Error: {str(e)}")
            return f"Error generating sales report: {str(e)}"
