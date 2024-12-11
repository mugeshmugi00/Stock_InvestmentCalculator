from django.shortcuts import render, redirect
import yfinance as yf
import pandas as pd
from datetime import datetime

# Main page where user inputs stock details
def main(request):
    if request.method == 'POST':
        # Retrieve the CSV file containing the stock tickers and weightages
        stocks_csv = request.FILES.get('stocks_file')
        
        if stocks_csv:
            try:
                # Read the CSV file
                stocks_data = pd.read_csv(stocks_csv)
                
                # Clean the data by keeping relevant columns and dropping others
                stocks_data = stocks_data[['Ticker', 'Weightage']].dropna()
                
                if not {'Ticker', 'Weightage'}.issubset(stocks_data.columns):
                    return render(request, 'main.html', {'error': 'Missing required columns in the file'})

                # Extract user input for investment and date range
                investment = float(request.POST.get('investment'))
                start_date = request.POST.get('start_date')
                end_date = request.POST.get('end_date')

                # Convert to datetime objects
                start_date = datetime.strptime(start_date, "%Y-%m-%d")
                end_date = datetime.strptime(end_date, "%Y-%m-%d")

                if start_date > end_date:
                    return render(request, 'main.html', {'error': 'Start date cannot be after end date'})

                # Calculate results
                results = {}
                for _, row in stocks_data.iterrows():
                    ticker = row['Ticker']
                    weightage = row['Weightage']
                    
                    # Fetch stock data from Yahoo Finance
                    stock = yf.Ticker(ticker)
                    data = stock.history(start=start_date, end=end_date)
                    
                    if data.empty:
                        continue  # Skip stock if no data available
                    
                    closing_prices = data['Close']
                    amount_to_invest = weightage * investment
                    shares_per_day = amount_to_invest / closing_prices
                    
                    results[ticker] = {
                        'Weightage': weightage,
                        'Investment': amount_to_invest,
                        'Shares': shares_per_day.to_dict()
                    }

                # Store results in session
                request.session['results'] = results
                return redirect('results')  # Redirect to results page
            except Exception as e:
                return render(request, 'main.html', {'error': f"An error occurred: {e}"})

        return render(request, 'main.html', {'error': 'No file uploaded'})

    return render(request, 'main.html')


# Results page to display calculated data
def results(request):
    results = request.session.get('results', None)
    
    if not results:
        return redirect('main')  # Redirect to main if no results found
    
    dates = set()
    for ticker_data in results.values():
        for date_key in ticker_data['Shares'].keys():
            if isinstance(date_key, str):  # Ensure it's a date string
                dates.add(date_key)
    
    dates = sorted(dates)

    return render(request, 'results.html', {'results': results, 'dates': dates})
