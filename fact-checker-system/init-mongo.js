// MongoDB initialization script
db = db.getSiblingDB('fact_checker');

// Create collections
db.createCollection('employees');

// Create indexes for better performance
db.employees.createIndex({ "department": 1 });
db.employees.createIndex({ "employment_status": 1 });
db.employees.createIndex({ "performance_score": 1 });

print('Database fact_checker initialized with employees collection and indexes');