#!/usr/bin/env python3
"""
CLI Testing Tool for SymPy Mathematical Functions

This tool allows direct testing of mathematical functions before
integrating them with the Luzia chat interface.
"""

import click
import json
from tools import ScratchPadTools
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

def print_result(result: dict, operation: str):
    """Print formatted result with colors."""
    print(f"\n{Fore.CYAN}=== {operation.upper()} RESULT ==={Style.RESET_ALL}")
    
    if result["status"] == "success":
        print(f"{Fore.GREEN}✅ Success{Style.RESET_ALL}")
        
        # Print relevant fields based on operation
        for key, value in result.items():
            if key != "status":
                print(f"{Fore.YELLOW}{key}:{Style.RESET_ALL} {value}")
    else:
        print(f"{Fore.RED}❌ Error{Style.RESET_ALL}")
        print(f"{Fore.RED}Message:{Style.RESET_ALL} {result.get('message', 'Unknown error')}")
    
    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}\n")

@click.group()
def cli():
    """CLI tool for testing SymPy mathematical functions."""
    pass

@cli.command()
@click.argument('equation')
@click.option('--variable', '-v', default='x', help='Variable to solve for (default: x)')
def solve(equation, variable):
    """Solve an algebraic equation.
    
    Examples:
        test_math_cli.py solve "2*x + 3 = 7"
        test_math_cli.py solve "x**2 - 4 = 0"
        test_math_cli.py solve "3*x + 2*y = 10" --variable y
    """
    tools = ScratchPadTools()
    result = tools.solve_equation(equation, variable)
    print_result(result, "equation solving")

@cli.command()
@click.argument('expression')
def simplify(expression):
    """Simplify a mathematical expression.
    
    Examples:
        test_math_cli.py simplify "(x**2 + 2*x + 1)/(x + 1)"
        test_math_cli.py simplify "sqrt(x**2)"
        test_math_cli.py simplify "sin(x)**2 + cos(x)**2"
    """
    tools = ScratchPadTools()
    result = tools.simplify_expression(expression)
    print_result(result, "expression simplification")

@cli.command()
@click.argument('expression')
@click.option('--variable', '-v', default='x', help='Variable to differentiate with respect to')
@click.option('--order', '-o', default=1, help='Order of derivative (default: 1)')
def derivative(expression, variable, order):
    """Calculate the derivative of an expression.
    
    Examples:
        test_math_cli.py derivative "x**3 + 2*x**2 - x + 1"
        test_math_cli.py derivative "sin(x)*cos(x)"
        test_math_cli.py derivative "x**4" --order 2
    """
    tools = ScratchPadTools()
    result = tools.calculate_derivative(expression, variable, order)
    print_result(result, "derivative calculation")

@cli.command()
@click.argument('expression')
@click.option('--variable', '-v', default='x', help='Variable to integrate with respect to')
@click.option('--limits', '-l', help='Integration limits as "lower,upper" (e.g., "0,1")')
def integral(expression, variable, limits):
    """Calculate the integral of an expression.
    
    Examples:
        test_math_cli.py integral "x**2"
        test_math_cli.py integral "sin(x)" --limits "0,pi"
        test_math_cli.py integral "2*x + 1" --limits "1,3"
    """
    tools = ScratchPadTools()
    
    # Parse limits if provided
    limits_list = None
    if limits:
        try:
            lower, upper = limits.split(',')
            limits_list = [lower.strip(), upper.strip()]
        except ValueError:
            print(f"{Fore.RED}Error: Limits must be in format 'lower,upper'{Style.RESET_ALL}")
            return
    
    result = tools.calculate_integral(expression, variable, limits_list)
    print_result(result, "integral calculation")

@cli.command()
@click.argument('expression')
def factor(expression):
    """Factor a polynomial expression.
    
    Examples:
        test_math_cli.py factor "x**2 + 2*x + 1"
        test_math_cli.py factor "x**3 - 8"
        test_math_cli.py factor "6*x**2 + 11*x + 3"
    """
    tools = ScratchPadTools()
    result = tools.factor_expression(expression)
    print_result(result, "expression factoring")

@cli.command()
@click.argument('expression')
def arithmetic(expression):
    """Calculate complex arithmetic expressions with high precision.
    
    Examples:
        test_math_cli.py arithmetic "222222+555555*10000"
        test_math_cli.py arithmetic "12345*67890"
        test_math_cli.py arithmetic "1111+2222+3333+4444"
    """
    tools = ScratchPadTools()
    result = tools.calculate_complex_arithmetic(expression)
    print_result(result, "complex arithmetic calculation")

@cli.command()
def test_all():
    """Run all planned test expressions to validate functionality."""
    
    print(f"{Fore.MAGENTA}🧪 Running Comprehensive Mathematical Function Tests{Style.RESET_ALL}\n")
    
    tools = ScratchPadTools()
    
    test_cases = [
        # Basic Algebra
        ("solve", "2*x + 3 = 7", {"variable": "x"}),
        ("solve", "x**2 - 4 = 0", {"variable": "x"}),
        ("solve", "3*x + 2*y = 10", {"variable": "x"}),
        
        # Expression Simplification
        ("simplify", "(x**2 + 2*x + 1)/(x + 1)", {}),
        ("simplify", "sqrt(x**2)", {}),
        ("simplify", "sin(x)**2 + cos(x)**2", {}),
        
        # Calculus
        ("derivative", "x**3 + 2*x**2 - x + 1", {"variable": "x", "order": 1}),
        ("derivative", "sin(x)*cos(x)", {"variable": "x", "order": 1}),
        ("integral", "x**2", {"variable": "x", "limits": None}),
        
        # Factoring
        ("factor", "x**2 + 2*x + 1", {}),
        
        # Complex Arithmetic
        ("arithmetic", "222222+555555*10000", {}),
        ("arithmetic", "12345*67890", {}),
        
        # Edge Cases
        ("solve", "x = x", {"variable": "x"}),
        ("solve", "x**2 + 1 = 0", {"variable": "x"}),
    ]
    
    passed = 0
    failed = 0
    
    for operation, expression, kwargs in test_cases:
        print(f"{Fore.BLUE}Testing {operation}: {expression}{Style.RESET_ALL}")
        
        try:
            if operation == "solve":
                result = tools.solve_equation(expression, kwargs.get("variable", "x"))
            elif operation == "simplify":
                result = tools.simplify_expression(expression)
            elif operation == "derivative":
                result = tools.calculate_derivative(expression, kwargs.get("variable", "x"), kwargs.get("order", 1))
            elif operation == "integral":
                result = tools.calculate_integral(expression, kwargs.get("variable", "x"), kwargs.get("limits"))
            elif operation == "factor":
                result = tools.factor_expression(expression)
            elif operation == "arithmetic":
                result = tools.calculate_complex_arithmetic(expression)
            
            if result["status"] == "success":
                print(f"  {Fore.GREEN}✅ PASSED{Style.RESET_ALL}")
                passed += 1
            else:
                print(f"  {Fore.RED}❌ FAILED: {result.get('message', 'Unknown error')}{Style.RESET_ALL}")
                failed += 1
                
        except Exception as e:
            print(f"  {Fore.RED}❌ EXCEPTION: {e}{Style.RESET_ALL}")
            failed += 1
        
        print()
    
    # Summary
    total = passed + failed
    print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}TEST SUMMARY:{Style.RESET_ALL}")
    print(f"  Total Tests: {total}")
    print(f"  {Fore.GREEN}Passed: {passed}{Style.RESET_ALL}")
    print(f"  {Fore.RED}Failed: {failed}{Style.RESET_ALL}")
    
    if failed == 0:
        print(f"\n{Fore.GREEN}🎉 All tests passed! Mathematical functions are ready for integration.{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.YELLOW}⚠️  Some tests failed. Review issues before proceeding.{Style.RESET_ALL}")

if __name__ == '__main__':
    cli() 