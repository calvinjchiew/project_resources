# CSCI E-51 Final Project Writeup
**The MiniML Language**<br>
Calvin J Chiew, Spring 2017

## Lexical Scoping Extension
As suggested by the project specification, I pursued the implementation of lexical scoping as an extension to the MiniML language. This was achieved by the use of closures, which bind functions to their lexical environment at definition time. During application, functions were evaluated based on their lexical environment, instead of the dynamic environment.

As a result, given the expression

```ocaml
let x = 1 in
let f = fun y -> x + y in
let x = 2 in
f 3 ;;`
```

the lexically scoped `eval_l` evaluator would return 4, similar to `eval_s` which is based on substitution semantics. In contrast, the dynamically scoped environment semantics evaluator `eval_d` would return 5.

To implement `eval_l`, I started by first copying `eval_d` and changing the match cases for `Fun` and `App`. However, since




