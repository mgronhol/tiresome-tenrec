#!/usr/bin/env python

import copy
#tokens = {}

LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
DIGITS = "0123456789"
WHITESPACE = " \n\r\t"

import pprint

#tokens['ID'] = ONE( LETTERS ) + MANY( OR( ONE( LETTERS ), ONE( DIGITS ) ) )
#tokens['NUMBER'] = MANY( DIGITS )



#
#  ----+----------+      +------
#      |          |      |
#      +-----+----+------+
#            |    |
#            +----+


class Feed( object ):
	def __init__( self, content ):
		self.content = content
		self.pos = 0
	
	def skip_whitespace( self ):
		global WHITESPACE
		while not self.empty() and self.peek() in WHITESPACE:
			self.skip()
	
	def next( self ):
		out = self.content[self.pos]
		self.pos += 1
		return out

	def peek( self ):
		return self.content[ self.pos ]
	
	def skip( self ):
		self.pos += 1
		
	def copy( self ):
		return Feed( self.content[ self.pos: ] )
		
	def empty( self ):
		return not ( self.pos < len( self.content ) )

class TerminalStack( object ):
	def __init__( self, content = [] ):
		self.content = content
		self.content = []
		self.counter = 0
	
	def incr( self ):
		self.counter += 1
		return self.counter

	def append( self, entry ):
		self.content.append( entry )
	
	def copy( self ):
		return TerminalStack( copy.deepcopy( self.content ) )
		#t = TerminalStack()
		#t.content = copy.deepcopy( self.content )
		#return t

	def set( self, stack ):
		self.content = copy.deepcopy( stack.content )


OK = True
NOK = False



def Character( charset ):
	def char_matcher( feed  ):
		if feed.empty():
			return NOK, None, None
		entry = feed.peek()
		
		if entry in charset:
			feed.skip()
			return OK, [entry], feed
		else:
			return NOK, None, None
	return char_matcher

def Keyword( keyword ):
	def keyword_matcher( feed  ):
		if feed.empty():
			return NOK, None, None
		
		new_feed = feed.copy()
		for k in keyword:
			entry = new_feed.next()
			if k != entry:
				return NOK, None, None
		return OK, keyword, new_feed
		
		
	return keyword_matcher


def Many( rule ):
	def many_matcher( feed ):
		out = []
		new_feed = feed.copy()
		last_saved = None
		while not new_feed.empty():	
			status, entry, new_feed2 = rule( new_feed )
			if status == OK:
				out = out + entry
				new_feed = new_feed2
				last_saved = new_feed2
				continue
			else:
				if len( out ) < 1:
					return NOK, None, None
				else:
					return OK, out, last_saved
		return OK, out, last_saved
	return many_matcher

def Or( *rules ):
	def or_matcher( feed ):
		for rule in rules:
			new_feed = feed.copy()
			
			new_feed.skip_whitespace()
			
			status, entry, new_feed2 = rule( new_feed )
			if status == OK:
				return OK, entry, new_feed2
		return NOK, None, None
	return or_matcher

def And( *rules ):
	def and_matcher( feed ):
		out = []
		new_feed = feed.copy()
		for rule in rules:
			new_feed.skip_whitespace()
			
			if new_feed.empty():
				return NOK, None, None
			
			
			status, entry, new_feed2 = rule( new_feed )
			if status != OK:
				return NOK, None, None
			out = out + entry
			new_feed = new_feed2
		return OK, out, new_feed
	return and_matcher

def R( tokens, key, stack ):
	def r_matcher( feed ):
		n = len( stack.content )
		id = stack.incr()
		stack.append( (key, n, id, None ) )
		status, content, new_feed = tokens[key]( feed )
		
		if status != OK:
			stack.append( (key, n, id, False ) )
		else:		
			stack.append( (key, n, id, True ) )
			if key[0].islower():
				content = [''.join(content)]
		
		return status, content, new_feed
	return r_matcher



class RuleEngine( object ):
	def __init__( self ):
		self.nonterminals = {}
		self.terminals = {}
		self.stack = TerminalStack()
	
	def add_nt( self, key, rule ):
		self.nonterminals[ key.lower() ] = rule
	
	def _or( self, *args ):
		rules = []
		for arg in args:
			if isinstance( arg, str ):
				if arg[0].isupper():
					rules.append( R( self.terminals, arg.upper(), self.stack ) )
				else:
					rules.append( R( self.nonterminals, arg.lower(), self.stack ) )
			else:
				rules.append( arg )
		return Or( *rules )
	
	def _and( self, *args ):
		rules = []
		for arg in args:
			if isinstance( arg, str ):
				if arg[0].isupper():
					rules.append( R( self.terminals, arg.upper(), self.stack ) )
				else:
					rules.append( R( self.nonterminals, arg.lower(), self.stack ) )
			else:
				rules.append( arg )
		return And( *rules )

	def _many( self, arg ):
		if isinstance( arg, str ):
			if arg[0].isupper():
				return Many( R( self.terminals, arg.upper(), self.stack ) )
			else:
				return Many( R( self.nonterminals, arg.lower(), self.stack ) )
		else:
			return Many( arg )
	
	
	def _parse_rule( self, rule ):
		if isinstance( rule, str ):
			if rule.startswith( '*' ):
				return self._many( self._parse_rule( rule[1:] ) )
			else:
				return rule
		else:
			#(op, rules) = rules
			op = rule[0]
			rules = rule[1:]
			if op == 'or':
				return self._or( *[ self._parse_rule( x ) for x in rules ] )
			elif op == 'and':
				return self._and( *[ self._parse_rule( x ) for x in rules ] )
			elif op == 'many':
				return self._many( self._parse_rule( rules[0] ) )


	def add_t( self, key, *args ):
		self.terminals[ key.upper() ] = self._and( *[ self._parse_rule( x ) for x in args ] )


	def _ast( self, results ):
		out = []
		current = []
		pos = 0
		key = False
		while pos < len( results ):
			if not key:
				key = results[pos]
				current.append( key )
				pos += 1
				continue
			if results[pos][2] != key[2] or results[pos][1] != key[1] :
				current.append( results[pos] )
			else:
				current.append( results[pos] )	
				if results[pos][3]:
					if key[0][0].islower():
						out.append( ( key[0], self.values[key[2]] ) )
					else:
						out.append( (key[0], self._ast( current[1:-1] ) ) )

					current = []
					key = None
				else:
					current = []
					key = None
			pos += 1
		return out


	def _branches( self, results ):
		out = []
		current = []
		pos = 0
		key = False
		while pos < len( results ):
			if not key:
				key = results[pos]
				current.append( key )
				pos += 1
				continue
			if results[pos][2] != key[2] or results[pos][1] != key[1] :
				current.append( results[pos] )
			else:
				current.append( results[pos] )	
				if results[pos][3]:
					if key[0][0].islower():
						out.extend( current )
					else:
						out.append( current[0] )
						out.extend( self._branches( current[1:-1] ) )
						out.append( current[-1] )
					current = []
					key = None
				else:
					current = []
					key = None
			pos += 1
		return out
	
	def parse( self, key, line ):
		# Ugly hack to please the gods of garbage collection and memory management
		del self.stack.content[:]
		status, content, new_feed = R( self.terminals, key.upper(), self.stack )( Feed( line ) )
		
		
		if status != OK:
			return None
		
		symbols = self._branches( self.stack.content )

		self.values = {}

		pos = 0
		for entry in symbols:
			if entry[-1]:
				if entry[0][0].islower():
					self.values[ entry[2] ] = ( content[pos])
					pos += 1
		
		return self._ast( self.stack.content )





		

number = Many( Character( DIGITS ) )
identifier = Or( And( Character( LETTERS ), Many( Character( DIGITS + LETTERS) ) ), Character( LETTERS ) )

#engine = RuleEngine()
#
#engine.add_nt( 'number', Many( Character( DIGITS ) ) )
#
#engine.add_nt( 'endl', Many( Character( ";" ) ) )
#
#engine.add_nt( 'identifier', And( Character( LETTERS ), Many( Character( DIGITS + LETTERS) ) ) )
#engine.add_nt( 'operator', Character( "+-*/" ) )
#
#engine.add_t( 'EXPR', 'number', 'operator', ('or', 'EXPR', 'number' )  )
#engine.add_t( 'STATEMENT', 'EXPR', 'endl' )
#
#
#pprint.pprint( engine.parse( 'STATEMENT', "1 + 2-3-4  ; " ) )
#pprint.pprint( engine.parse( 'STATEMENT', "1+1+1+1+1;" ) )



