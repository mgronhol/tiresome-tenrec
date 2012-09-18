#!/usr/bin/env python


import RuleEngine

import pprint


engine = RuleEngine.RuleEngine()

engine.add_nt( 'number', RuleEngine.number )
engine.add_nt( 'idn', RuleEngine.identifier )
engine.add_nt( 'operator', RuleEngine.Character( "-+*/" ) )
engine.add_nt( 'equals', RuleEngine.Character( "=" ) )

engine.add_nt( 'left_paren', RuleEngine.Character( "(" ) )
engine.add_nt( 'right_paren', RuleEngine.Character( ")" ) )

engine.add_nt( 'dot', RuleEngine.Character( "." ) )

engine.add_t( 'REAL', 'number', 'dot', 'number' )

engine.add_t( 'VALUE', ('or', 'REAL', 'number' , 'idn' ) )

engine.add_t( 'SINGLE-EXPR', ('or', 'PAREN-EXPR', 'VALUE' ), 'operator', ('or', 'EXPR', 'VALUE' ) )

engine.add_t( 'PAREN-EXPR', 'left_paren', ('or', 'PAREN-EXPR', 'SINGLE-EXPR', 'VALUE' ), 'right_paren' )

engine.add_t( 'EXPR', ('or', 'SINGLE-EXPR', 'PAREN-EXPR' ) )

engine.add_t( 'ASSIGN', 'idn', 'equals', ('or', 'EXPR', 'VALUE' ) )

engine.add_t( 'STMT', ('or', 'ASSIGN', 'EXPR', 'VALUE' ) )


symbol_table = {}


def Eval( entry ):
	global symbol_table
	(op, params) = entry

	if op == "VALUE":
		return Eval( params[0] )

	elif op == "number":
		return int( params )

	elif op == "idn":
		return symbol_table[ params ]
	
	elif op == 'REAL':
		p = Eval( params[0] )
		q = Eval( params[2] )
		return p + float(q ) / (10**len( params[2][1] ) )
	
	elif op == "SINGLE-EXPR":
		lhs = Eval( params[0] )
		oper = params[1]
		rhs = Eval( params[2] )
		if oper[1] == "+":
			return lhs + rhs
		elif oper[1] == "-":
			return lhs - rhs
		elif oper[1] == "*":
			return lhs * rhs
		elif oper[1] == "/":
			return lhs / rhs

	elif op == "EXPR":
		return Eval( params[0] )

	elif op == "STMT":
		return Eval( params[0] )
		
	elif op == "ASSIGN":
		key = params[0][1]
		symbol_table[ key ] = Eval( params[2] )
		return "%s = %i"%( key, symbol_table[ key ] )
	
	elif op == "PAREN-EXPR":
		return Eval( params[1] )


try:
	while True:
		line = raw_input(">")
		result = engine.parse( 'STMT', line )
		pprint.pprint( result )
		print "Result:", Eval( result[0] )

except KeyboardInterrupt:
	pass
print ""
