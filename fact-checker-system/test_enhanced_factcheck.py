#!/usr/bin/env python3
"""
Test script for enhanced fact-checking capabilities

This script demonstrates the improved RAG agent's ability to fact-check
specific numerical claims and demographic comparisons.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

from agents.enhanced_rag_agent import EnhancedRAGAgent

def test_enhanced_fact_checking():
    """Test various types of factual claims"""
    
    print("🧪 Testing Enhanced Fact-Checking Capabilities")
    print("=" * 60)
    
    try:
        agent = EnhancedRAGAgent()
        print("✅ Connected to database successfully")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        print("💡 Make sure MongoDB is running: docker-compose up -d")
        return
    
    # Test statements with specific claims to verify
    test_statements = [
        # Gender comparison claims
        {
            "statement": "Our company has more females than males",
            "category": "Gender Comparison",
            "expected": "Should verify actual M/F ratio"
        },
        {
            "statement": "Production department has more males than females", 
            "category": "Department Gender",
            "expected": "Should check production department gender split"
        },
        {
            "statement": "IT department is mostly male",
            "category": "Department Gender",
            "expected": "Should verify if IT has more males"
        },
        
        # Employee count claims
        {
            "statement": "Our company has exactly 311 employees",
            "category": "Employee Count",
            "expected": "Should verify total employee count"
        },
        {
            "statement": "Production department has more than 100 employees",
            "category": "Department Count", 
            "expected": "Should check production department size"
        },
        {
            "statement": "Sales department has less than 50 employees",
            "category": "Department Count",
            "expected": "Should verify sales department size"
        },
        
        # Salary claims
        {
            "statement": "Our company average salary is $70000",
            "category": "Salary Verification",
            "expected": "Should verify against actual average salary"
        },
        {
            "statement": "Production department average salary is over $60000",
            "category": "Department Salary",
            "expected": "Should check production department salaries"
        },
        {
            "statement": "IT department average salary is $80000",
            "category": "Department Salary", 
            "expected": "Should verify IT department average salary"
        },
        
        # Complex claims
        {
            "statement": "Engineering department has more than 20 employees with average salary over $75000",
            "category": "Complex Claim",
            "expected": "Should verify both count and salary for engineering"
        }
    ]
    
    print(f"\n🔍 Testing {len(test_statements)} different claim types:")
    print("-" * 60)
    
    for i, test in enumerate(test_statements, 1):
        print(f"\n{i}. {test['category']}: {test['statement']}")
        print(f"   Expected: {test['expected']}")
        
        try:
            result = agent.fact_check_statement(test['statement'])
            
            print(f"   Analysis Type: {result.get('analysis_type', 'unknown')}")
            
            if 'claim_verified' in result:
                verification = "✅ VERIFIED" if result['claim_verified'] else "❌ FALSE"
                print(f"   Verification: {verification}")
                
                if 'verification_details' in result:
                    print(f"   Details: {result['verification_details']}")
            
            # Show key data
            if 'data' in result and isinstance(result['data'], dict):
                data = result['data']
                if 'gender_counts' in data:
                    print(f"   Gender Data: {data['gender_counts']}")
                elif 'average_salary' in data:
                    print(f"   Salary Data: {data['avg_salary_formatted']}")
                elif 'actual_employee_count' in data:
                    print(f"   Employee Count: {data['actual_employee_count']}")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        
        print("-" * 40)
    
    # Test some baseline data
    print(f"\n📊 Baseline Data Check:")
    print("-" * 30)
    
    try:
        # Get overall company stats
        company_gender = agent.get_gender_distribution()
        company_salary = agent.get_salary_stats()
        
        print(f"Total Employees: {company_gender['total_employees']}")
        print(f"Gender Split: {company_gender['gender_ratio']}")
        print(f"Average Salary: {company_salary['avg_salary_formatted']}")
        
        # Check a few departments
        for dept in ["Production", "IT", "Sales"]:
            try:
                dept_stats = agent.get_department_stats(dept)
                if 'error' not in dept_stats:
                    print(f"{dept}: {dept_stats['total_employees']} employees, {dept_stats.get('gender_ratio', 'N/A')} M/F")
            except:
                print(f"{dept}: Data not available")
                
    except Exception as e:
        print(f"❌ Error getting baseline data: {e}")
    
    print(f"\n🎉 Enhanced fact-checking test completed!")
    print("💡 Now you can test these types of statements in the web UI")

if __name__ == "__main__":
    test_enhanced_fact_checking()