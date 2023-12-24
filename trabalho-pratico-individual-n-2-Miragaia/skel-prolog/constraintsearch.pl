
:- discontiguous domain/3, has_constraint/3.

%% -------------------------------------
%% Constraint search 
%% -------------------------------------

search(Problem,Solution)
:- findall((V,Domain), domain(Problem,V,Domain), VarVals),
   search(Problem,VarVals,Solution).

search(_,VarVals,_) % check if there is an empty domain
:- member((_,[]),VarVals), !, fail.

search(Prob,VarVals,Solution) % if all domains have 
                              % exactly one value
:- \+ ( member((_,Vals),VarVals), 
        length(Vals,Len), Len\=1 ), !, 
   findall((V,Val),member((V,[Val]),VarVals),Solution),
   \+ ( has_constraint(Prob,(V1,V2),ConstraintName),
        member((V1,X1),Solution),
        member((V2,X2),Solution),
        ConstraintCall =.. [ConstraintName,V1,X1,V2,X2],
        \+ ConstraintCall ).

search(Prob,VarVals,Solution) % continue expansion
:- findall((V,X),( member((V,Vals),VarVals),
                   length(Vals,Len), Len>1,
                   member(X,Vals) ),Pairs),
   search_step(Prob,Pairs,VarVals,NewVarVals),
   search(Prob,NewVarVals,Solution).

%

search_step(_,[(V,X)|_],VarVals,[(V,[X])|NewVarVals])
:- select((V,_),VarVals,NewVarVals).
search_step(_,[_|Pairs],VarVals,NewVarVals)
:- search_step(_,Pairs,VarVals,NewVarVals).


