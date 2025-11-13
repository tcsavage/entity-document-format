# Parser

One of the reasons this project exists is as an excuse and vehicle to learn abut the parsing strategy employed by the [Carbon toolchain](https://github.com/carbon-language/carbon-lang/blob/580e84513c804ba10127f287159bc1279b62f2aa/toolchain/docs/parse.md) (see also [this talk by Chandler Carruth](https://www.youtube.com/watch?v=ZI198eFghJkO)). It's an interesting technique with several advantages that makes sense for Carbon, but realistically maybe not for this project. Although it may not be completely unique to Carbon, I'm going to refer to it as the Carbon-style strategy.

This parser doesn't produce an AST, but rather a parse tree represented as a flat list of nodes in a 1:1 correspondence with the list of tokens being parsed. (I.e. every token has a corresponding parse tree node, but the order may be different.) Each node is of one of three types:

- A leaf node with zero children
- A node with a fixed number of children (e.g. a binary operator has 2 children)
- A node with a variable number of children delimited by a bracketing start token

# The EDF parser

If you watch Chandler's talk, you'll hear him mention changes made to the language (in particular the introduction of new introducers) in order to make parsing easier. Having implemented the Carbon-style parser for EDF I now have a better understanding of why that's important.

EDF doesn't have introducers in the way that Carbon does (e.g. `var`, `fn`, etc.). Instead every block and attribute is introduced by an identifier. That's challenging enough because it requires either look-ahead or backtracking, but it's even less desireable under the Carbon-style parser because bracketing.

What you really want is for every variable-sized node to be bracketed by an introducer and a terminator. In Carbon the introducer is some kind of keyword (e.g. `var`) and the terminator is a semicolon (or brace?). This structure is quite nice to work with in the parser.
