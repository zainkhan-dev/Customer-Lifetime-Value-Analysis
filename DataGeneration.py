import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Configuration parameters
start_date = datetime(2022, 1, 1)
end_date = datetime(2024, 12, 31)
n_customers = 2000
n_transactions = 15000

# Product categories and their characteristics
products = {
    'Electronics': {'avg_price': 250, 'std_price': 150, 'frequency': 0.25},
    'Clothing': {'avg_price': 80, 'std_price': 40, 'frequency': 0.30},
    'Home & Garden': {'avg_price': 120, 'std_price': 80, 'frequency': 0.20},
    'Books': {'avg_price': 25, 'std_price': 15, 'frequency': 0.15},
    'Sports': {'avg_price': 95, 'std_price': 60, 'frequency': 0.10}
}

# Customer segments (realistic business scenario)
customer_segments = {
    'High Value': {
        'proportion': 0.15,
        'avg_annual_orders': 12,
        'avg_order_value_multiplier': 2.5,
        'churn_rate': 0.05
    },
    'Medium Value': {
        'proportion': 0.35,
        'avg_annual_orders': 6,
        'avg_order_value_multiplier': 1.2,
        'churn_rate': 0.15
    },
    'Low Value': {
        'proportion': 0.35,
        'avg_annual_orders': 3,
        'avg_order_value_multiplier': 0.8,
        'churn_rate': 0.25
    },
    'One-time Buyers': {
        'proportion': 0.15,
        'avg_annual_orders': 1,
        'avg_order_value_multiplier': 0.9,
        'churn_rate': 0.80
    }
}

def generate_customers():
    """Generate customer master data"""
    customers = []
    
    for i in range(1, n_customers + 1):
        # Assign customer to segment
        segment = np.random.choice(
            list(customer_segments.keys()),
            p=[customer_segments[seg]['proportion'] for seg in customer_segments.keys()]
        )
        
        # Generate acquisition date (more customers acquired recently)
        days_from_start = np.random.exponential(300)  # Exponential distribution
        days_from_start = min(days_from_start, (end_date - start_date).days)
        acquisition_date = start_date + timedelta(days=int(days_from_start))
        
        # Customer demographics
        age = np.random.normal(35, 12)
        age = max(18, min(70, age))  # Constrain age
        
        cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 
                 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose']
        
        customers.append({
            'customer_id': f'CUST_{i:04d}',
            'acquisition_date': acquisition_date.strftime('%Y-%m-%d'),
            'segment': segment,
            'age': int(age),
            'city': random.choice(cities),
            'is_active': True
        })
    
    return pd.DataFrame(customers)

def generate_transactions(customers_df):
    """Generate realistic transaction data"""
    transactions = []
    transaction_id = 1
    
    for _, customer in customers_df.iterrows():
        customer_id = customer['customer_id']
        acquisition_date = datetime.strptime(customer['acquisition_date'], '%Y-%m-%d')
        segment = customer['segment']
        segment_data = customer_segments[segment]
        
        # Determine if customer churned and when
        churned = np.random.random() < segment_data['churn_rate']
        if churned:
            churn_date = acquisition_date + timedelta(
                days=np.random.exponential(180)  # Average 6 months before churn
            )
            churn_date = min(churn_date, end_date)
        else:
            churn_date = end_date
        
        # Generate transactions for this customer
        active_period = (churn_date - acquisition_date).days
        if active_period <= 0:
            continue
            
        # Number of orders based on segment
        avg_annual_orders = segment_data['avg_annual_orders']
        expected_orders = max(1, int(avg_annual_orders * active_period / 365))
        n_orders = np.random.poisson(expected_orders)
        
        if segment == 'One-time Buyers':
            n_orders = 1
        
        # Generate order dates
        order_dates = []
        for _ in range(n_orders):
            days_offset = np.random.uniform(0, active_period)
            order_date = acquisition_date + timedelta(days=days_offset)
            order_dates.append(order_date)
        
        order_dates.sort()
        
        # Generate transactions for each order
        for order_date in order_dates:
            if order_date > end_date:
                continue
                
            # Number of items in this order (1-5 items)
            items_in_order = np.random.choice([1, 2, 3, 4, 5], p=[0.4, 0.3, 0.2, 0.08, 0.02])
            
            for _ in range(items_in_order):
                # Select product category
                category = np.random.choice(
                    list(products.keys()),
                    p=[products[cat]['frequency'] for cat in products.keys()]
                )
                
                # Generate price based on category and customer segment
                base_price = np.random.normal(
                    products[category]['avg_price'],
                    products[category]['std_price']
                )
                base_price = max(5, base_price)  # Minimum price
                
                # Apply segment multiplier
                final_price = base_price * segment_data['avg_order_value_multiplier']
                
                # Add some seasonality (higher prices in Q4)
                if order_date.month in [11, 12]:
                    final_price *= np.random.uniform(1.1, 1.3)
                
                transactions.append({
                    'transaction_id': f'TXN_{transaction_id:06d}',
                    'customer_id': customer_id,
                    'transaction_date': order_date.strftime('%Y-%m-%d'),
                    'product_category': category,
                    'amount': round(final_price, 2),
                    'year': order_date.year,
                    'month': order_date.month,
                    'quarter': f'Q{(order_date.month-1)//3 + 1}'
                })
                transaction_id += 1
    
    return pd.DataFrame(transactions)

def add_realistic_patterns(transactions_df):
    """Add realistic business patterns to the data"""
    # Add customer behavior patterns
    transactions_df['day_of_week'] = pd.to_datetime(transactions_df['transaction_date']).dt.day_name()
    transactions_df['is_weekend'] = pd.to_datetime(transactions_df['transaction_date']).dt.dayofweek >= 5
    
    # Add discount indicator (10% of transactions have discounts)
    transactions_df['has_discount'] = np.random.choice([True, False], 
                                                      size=len(transactions_df), 
                                                      p=[0.1, 0.9])
    
    # Apply discount
    discount_mask = transactions_df['has_discount']
    transactions_df.loc[discount_mask, 'discount_amount'] = (
        transactions_df.loc[discount_mask, 'amount'] * np.random.uniform(0.05, 0.25, discount_mask.sum())
    ).round(2)
    
    transactions_df['discount_amount'] = transactions_df['discount_amount'].fillna(0)
    transactions_df['final_amount'] = transactions_df['amount'] - transactions_df['discount_amount']
    
    return transactions_df

# Generate the datasets
print("Generating customer data...")
customers_df = generate_customers()

print("Generating transaction data...")
transactions_df = generate_transactions(customers_df)

print("Adding realistic patterns...")
transactions_df = add_realistic_patterns(transactions_df)

# Create summary statistics
print("\n=== DATASET SUMMARY ===")
print(f"Total Customers: {len(customers_df):,}")
print(f"Total Transactions: {len(transactions_df):,}")
print(f"Date Range: {transactions_df['transaction_date'].min()} to {transactions_df['transaction_date'].max()}")
print(f"Total Revenue: ${transactions_df['final_amount'].sum():,.2f}")

print("\nCustomer Segments:")
print(customers_df['segment'].value_counts())

print("\nProduct Categories:")
print(transactions_df['product_category'].value_counts())

print("\nMonthly Transaction Volume (last 12 months):")
recent_transactions = transactions_df[pd.to_datetime(transactions_df['transaction_date']) >= '2024-01-01']
monthly_stats = recent_transactions.groupby(['year', 'month']).agg({
    'transaction_id': 'count',
    'final_amount': 'sum'
}).round(2)
print(monthly_stats.tail(12))

# Save datasets
customers_df.to_csv('customers.csv', index=False)
transactions_df.to_csv('transactions.csv', index=False)

print("\n=== FILES SAVED ===")
print("✓ customers.csv")
print("✓ transactions.csv")

print("\n=== NEXT STEPS ===")
print("1. Load the data: pd.read_csv('customers.csv'), pd.read_csv('transactions.csv')")
print("2. Start with basic EDA (Exploratory Data Analysis)")
print("3. Calculate RFM metrics (Recency, Frequency, Monetary)")
print("4. Compute Customer Lifetime Value")
print("5. Perform customer segmentation")
print("6. Create visualizations and insights")