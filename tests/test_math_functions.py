#!/usr/bin/env python3
"""
Unit tests for mathematical functions in MathTools.
"""

import pytest
import sympy
import os
from tools.math_tools import MathTools


@pytest.fixture
def math_tools():
    """Create MathTools instance for testing."""
    # Set a test API key
    os.environ['OPENAI_API_KEY'] = 'test-key'
    return MathTools()


class TestMathFunctions:
    """Test mathematical operations and expression parsing."""
    
    @pytest.mark.unit
    def test_parse_expression_safely_basic(self, math_tools):
        """Test basic expression parsing."""
        # Basic expressions
        result = math_tools._parse_expression_safely("x + 2")
        assert str(result) == "x + 2"
        
        result = math_tools._parse_expression_safely("2*x + 3")
        assert str(result) == "2*x + 3"
    
    @pytest.mark.unit
    def test_parse_expression_safely_caret_to_power(self, math_tools):
        """Test conversion of ^ to ** for exponentiation."""
        result = math_tools._parse_expression_safely("x^2")
        assert str(result) == "x**2"
        
        result = math_tools._parse_expression_safely("2*x^3 + x^2")
        assert str(result) == "2*x**3 + x**2"
    
    @pytest.mark.unit
    def test_parse_expression_safely_implicit_multiplication(self, math_tools):
        """Test implicit multiplication handling."""
        # 3x should become 3*x
        result = math_tools._parse_expression_safely("3x")
        assert str(result) == "3*x"
        
        # Multiple variables
        result = math_tools._parse_expression_safely("2x + 3y")
        assert str(result) == "2*x + 3*y"
        
        # With parentheses: )x should become )*x
        result = math_tools._parse_expression_safely("(x+1)y")
        assert str(result) == "(x + 1)*y"
    
    @pytest.mark.unit
    def test_parse_expression_safely_preserve_functions(self, math_tools):
        """Test that function names are preserved (sin, cos, etc.)."""
        result = math_tools._parse_expression_safely("sin(x)")
        assert str(result) == "sin(x)"
        
        result = math_tools._parse_expression_safely("cos(x) + sin(x)")
        assert str(result) == "sin(x) + cos(x)"
        
        result = math_tools._parse_expression_safely("log(x) + exp(x)")
        assert str(result) == "exp(x) + log(x)"
    
    @pytest.mark.unit
    def test_parse_expression_safely_invalid_expression(self, math_tools):
        """Test handling of invalid expressions."""
        with pytest.raises(ValueError, match="Invalid mathematical expression"):
            math_tools._parse_expression_safely("invalid_expression_with_$%@")
    
    @pytest.mark.unit
    def test_solve_equation_basic(self, math_tools, sample_test_cases):
        """Test basic equation solving."""
        for equation, variable, expected_solutions in sample_test_cases["equations"]:
            result = math_tools.solve_equation(equation, variable)
            
            assert result["status"] == "success"
            assert result["equation"] == equation
            assert result["variable"] == variable
            assert result["solutions"] == expected_solutions
            assert result["solution_type"] == "symbolic"
    
    @pytest.mark.unit
    def test_solve_equation_without_equals(self, math_tools):
        """Test solving equations without explicit = sign (assumes = 0)."""
        result = math_tools.solve_equation("x**2 - 4", "x")
        
        assert result["status"] == "success"
        assert sorted(result["solutions"]) == ["-2", "2"]
    
    @pytest.mark.unit
    def test_solve_equation_no_solutions(self, math_tools):
        """Test equation with no real solutions."""
        result = math_tools.solve_equation("x**2 + 1 = 0", "x")
        
        assert result["status"] == "success"
        # Complex solutions
        assert len(result["solutions"]) == 2
        assert "I" in str(result["solutions"])
    
    @pytest.mark.unit
    def test_solve_equation_invalid(self, math_tools):
        """Test handling of invalid equations."""
        result = math_tools.solve_equation("invalid$equation", "x")
        
        assert result["status"] == "error"
        assert "Invalid mathematical expression" in result["message"]
    
    @pytest.mark.unit
    def test_simplify_expression_basic(self, math_tools, sample_test_cases):
        """Test basic expression simplification."""
        for expression, expected in sample_test_cases["expressions"]:
            result = math_tools.simplify_expression(expression)
            
            assert result["status"] == "success"
            assert result["original_expression"] == expression
            # Note: SymPy may format results differently, so we check semantic equivalence
            simplified = sympy.simplify(sympy.parse_expr(result["simplified_expression"]))
            expected_simplified = sympy.simplify(sympy.parse_expr(expected))
            assert simplified.equals(expected_simplified) or str(simplified) == expected
    
    @pytest.mark.unit
    def test_simplify_expression_already_simplified(self, math_tools):
        """Test simplifying an already simplified expression."""
        result = math_tools.simplify_expression("x + 1")
        
        assert result["status"] == "success"
        assert result["simplified_expression"] == "x + 1"
        assert result["is_simplified"] == False  # No change needed
    
    @pytest.mark.unit
    def test_simplify_expression_invalid(self, math_tools):
        """Test handling of invalid expressions for simplification."""
        result = math_tools.simplify_expression("invalid$expression")
        
        assert result["status"] == "error"
        assert "Invalid mathematical expression" in result["message"]
    
    @pytest.mark.unit
    def test_calculate_derivative_basic(self, math_tools, sample_test_cases):
        """Test basic derivative calculations."""
        for expression, variable, order, expected in sample_test_cases["derivatives"]:
            result = math_tools.calculate_derivative(expression, variable, order)
            
            assert result["status"] == "success"
            assert result["original_expression"] == expression
            assert result["variable"] == variable
            assert result["order"] == order
            
            # Check semantic equivalence
            calculated = sympy.parse_expr(result["derivative"])
            expected_expr = sympy.parse_expr(expected)
            assert calculated.equals(expected_expr) or str(calculated) == expected
    
    @pytest.mark.unit
    def test_calculate_derivative_first_order_default(self, math_tools):
        """Test that first order is default for derivatives."""
        result = math_tools.calculate_derivative("x**3")
        
        assert result["status"] == "success"
        assert result["order"] == 1
        assert result["derivative"] == "3*x**2"
    
    @pytest.mark.unit
    def test_calculate_derivative_higher_order(self, math_tools):
        """Test higher order derivatives."""
        result = math_tools.calculate_derivative("x**4", "x", 2)
        
        assert result["status"] == "success"
        assert result["order"] == 2
        assert result["derivative"] == "12*x**2"
    
    @pytest.mark.unit
    def test_calculate_derivative_invalid(self, math_tools):
        """Test handling of invalid expressions for derivatives."""
        result = math_tools.calculate_derivative("invalid$expression")
        
        assert result["status"] == "error"
        assert "Invalid mathematical expression" in result["message"]
    
    @pytest.mark.unit
    def test_calculate_integral_indefinite(self, math_tools):
        """Test indefinite integral calculations."""
        result = math_tools.calculate_integral("x**2", "x")
        
        assert result["status"] == "success"
        assert result["original_expression"] == "x**2"
        assert result["variable"] == "x"
        assert result["limits"] == None
        assert result["integral_type"] == "indefinite"
        assert result["integral"] == "x**3/3"
    
    @pytest.mark.unit
    def test_calculate_integral_definite(self, math_tools):
        """Test definite integral calculations."""
        result = math_tools.calculate_integral("x**2", "x", ["0", "1"])
        
        assert result["status"] == "success"
        assert result["limits"] == ["0", "1"]
        assert result["integral_type"] == "definite"
        # Definite integral of x^2 from 0 to 1 is 1/3
        assert result["integral"] == "1/3"
    
    @pytest.mark.unit
    def test_calculate_integral_invalid_limits(self, math_tools):
        """Test handling of invalid limits for definite integrals."""
        result = math_tools.calculate_integral("x**2", "x", ["0"])  # Only one limit
        
        assert result["status"] == "error"
        assert "Limits must be a list of exactly 2 values" in result["message"]
    
    @pytest.mark.unit
    def test_calculate_integral_invalid_expression(self, math_tools):
        """Test handling of invalid expressions for integration."""
        result = math_tools.calculate_integral("invalid$expression")
        
        assert result["status"] == "error"
        assert "Invalid mathematical expression" in result["message"]
    
    @pytest.mark.unit
    def test_factor_expression_basic(self, math_tools, sample_test_cases):
        """Test basic polynomial factoring."""
        for expression, expected in sample_test_cases["factors"]:
            result = math_tools.factor_expression(expression)
            
            assert result["status"] == "success"
            assert result["original_expression"] == expression
            
            # Check semantic equivalence by expanding both forms
            factored = sympy.parse_expr(result["factored_expression"])
            expected_factored = sympy.parse_expr(expected)
            original = sympy.parse_expr(expression)
            
            # Verify factorization is correct by expanding
            assert sympy.expand(factored).equals(original)
            # Verify it matches expected format (may have different ordering)
            assert sympy.expand(factored).equals(sympy.expand(expected_factored))
    
    @pytest.mark.unit
    def test_factor_expression_already_factored(self, math_tools):
        """Test factoring an already factored expression."""
        result = math_tools.factor_expression("(x + 1)*(x + 2)")
        
        assert result["status"] == "success"
        # Should remain the same or equivalent
        factored = sympy.parse_expr(result["factored_expression"])
        original = sympy.parse_expr("(x + 1)*(x + 2)")
        assert sympy.expand(factored).equals(sympy.expand(original))
    
    @pytest.mark.unit
    def test_factor_expression_irreducible(self, math_tools):
        """Test factoring an irreducible polynomial."""
        result = math_tools.factor_expression("x**2 + 1")
        
        assert result["status"] == "success"
        # Over reals, x^2 + 1 is irreducible
        assert result["factored_expression"] == "x**2 + 1"
    
    @pytest.mark.unit
    def test_factor_expression_invalid(self, math_tools):
        """Test handling of invalid expressions for factoring."""
        result = math_tools.factor_expression("invalid$expression")
        
        assert result["status"] == "error"
        assert "Invalid mathematical expression" in result["message"]
    
    @pytest.mark.unit
    def test_calculate_complex_arithmetic_basic(self, math_tools, sample_test_cases):
        """Test complex arithmetic calculations."""
        for expression, expected in sample_test_cases["arithmetic"]:
            result = math_tools.calculate_complex_arithmetic(expression)
            
            assert result["status"] == "success"
            assert result["original_expression"] == expression
            assert result["result"] == expected
            assert result["result_type"] == "arithmetic"
            assert result["precision"] == "high"
    
    @pytest.mark.unit
    def test_calculate_complex_arithmetic_large_numbers(self, math_tools):
        """Test arithmetic with very large numbers."""
        result = math_tools.calculate_complex_arithmetic("999999999*888888888")
        
        assert result["status"] == "success"
        assert result["result"] == 999999999 * 888888888
        assert isinstance(result["result"], int)
    
    @pytest.mark.unit
    def test_calculate_complex_arithmetic_decimal_precision(self, math_tools):
        """Test arithmetic with high decimal precision."""
        result = math_tools.calculate_complex_arithmetic("1.123456789*2.987654321")
        
        assert result["status"] == "success"
        assert isinstance(result["result"], float)
        # Check reasonable precision
        expected = 1.123456789 * 2.987654321
        assert abs(result["result"] - expected) < 1e-10
    
    @pytest.mark.unit
    def test_calculate_complex_arithmetic_invalid_expression(self, math_tools):
        """Test handling of invalid arithmetic expressions."""
        result = math_tools.calculate_complex_arithmetic("invalid_expression")
        
        assert result["status"] == "error"
        assert "Error calculating arithmetic expression" in result["message"]


class TestExpressionParsingSecurity:
    """Test security aspects of expression parsing."""
    
    @pytest.mark.unit
    def test_dangerous_input_filtered(self, math_tools):
        """Test that dangerous characters are filtered out."""
        # These should be cleaned of dangerous characters
        dangerous_inputs = [
            "__import__('os').system('rm -rf /')",
            "eval('malicious_code')",
            "exec('dangerous_code')"
        ]
        
        for dangerous_input in dangerous_inputs:
            # Should either raise ValueError or return cleaned result
            try:
                result = math_tools._parse_expression_safely(dangerous_input)
                # If it doesn't raise an error, the result should be cleaned
                assert "__import__" not in str(result)
                assert "eval" not in str(result)
                assert "exec" not in str(result)
            except ValueError:
                # This is acceptable - dangerous input rejected
                pass
    
    @pytest.mark.unit
    def test_only_mathematical_characters_allowed(self, math_tools):
        """Test that only mathematical characters are preserved."""
        # Input with mixed valid/invalid characters
        input_expr = "2*x + 3 - $invalidchar% + y"
        
        try:
            result = math_tools._parse_expression_safely(input_expr)
            # Should only contain mathematical characters
            result_str = str(result)
            assert "$" not in result_str
            assert "%" not in result_str
            # Valid math characters should remain
            assert "x" in result_str
            assert "y" in result_str
            assert "+" in result_str or "*" in result_str
        except ValueError:
            # Also acceptable - invalid input rejected
            pass 