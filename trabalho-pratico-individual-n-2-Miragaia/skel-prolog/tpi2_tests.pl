
:- [tpi2].

write2ln(X)
:- writeln(X), nl.

%% ------------------------------------------------------------
%% Semantic network
%% ------------------------------------------------------------

:- retractall(declared(_,_)), retractall(assoc_stats(_,_,_,_)).

:- declare(descartes,subtype(human,mammal)).
:- declare(descartes,member('Socrates',man)).
:- declare(descartes,member('Aristoteles',man)).
:- declare(descartes,member('Plato',man)).
:- declare(descartes,association('Socrates',teacher,'Philosophy')).
:- declare(descartes,association('Socrates',teacher,'Mathematics')).
:- declare(descartes,association('Plato',teacher,'Philosophy')).
:- declare(darwin,subtype(man,human)).
:- declare(darwin,association(mammal,breastfeed,'Yes')).
:- declare(darwin,association(man,likes,meat)).
:- declare(darwin,subtype(mammal,vertebrate)).
:- declare(yesao,association('Socrates',teacher,'Mathematics')).
:- declare(yesao,association('Plato',teacher,'Philosophy')).
:- declare(damasio, association(philosopher,likes,'Philosophy')).

%% query_local

:- query_local(_,_,_,_,Declarations),
   write2ln('all declarations':Declarations).
:- query_local(_,_,subtype,man,Declarations),
   write2ln(subtype-man:Declarations).
:- query_local(_,_,member,man,Declarations),
   write2ln(member-man:Declarations).

%% query

:- query('Socrates',likes,Declarations),
   write2ln('Socrates'-likes:Declarations).

%% update_assoc_stats

:- update_assoc_stats(teacher,descartes),
   assoc_stats(teacher,descartes,Stats1,Stats2),
   write2ln((teacher,descartes):(Stats1,Stats2)).

:- declare(descartes,member('Philosophy',discipline)).

:- update_assoc_stats(teacher,descartes),
   assoc_stats(teacher,descartes,Stats1,Stats2),
   write2ln((teacher,descartes):(Stats1,Stats2)).

:- declare(descartes,subtype(man,human)).

:- update_assoc_stats(teacher,descartes),
   assoc_stats(teacher,descartes,Stats1,Stats2),
   write2ln((teacher,descartes):(Stats1,Stats2)).

:- declare(descartes,member('Elvira',woman)).
:- declare(descartes,association('Elvira',teacher,'Philosophy')).

:- update_assoc_stats(teacher,descartes),
   assoc_stats(teacher,descartes,Stats1,Stats2),
   write2ln((teacher,descartes):(Stats1,Stats2)).

%% query

:- declare(descartes,subtype(woman,human)).

:- query('Elvira',breastfeed,Declarations),
   write2ln(Declarations).

%% update_assoc_stats

:- update_assoc_stats(teacher,descartes),
   assoc_stats(teacher,descartes,Stats1,Stats2),
   write2ln((teacher,descartes):(Stats1,Stats2)).

%% query_local

:- declare(darwin,assocOne('Mary',hasMother,'Elvira')).
:- declare(darwin,assocOne('Elvira',hasMother,'Eva')).

:- query_local(_,_,hasMother,_,Declarations),
   write2ln('hasMother':Declarations).

%% update_assoc_stats

:- update_assoc_stats(hasMother,darwin),
   assoc_stats(hasMother,darwin,Stats1,Stats2),
   write2ln((hasMother,darwin):(Stats1,Stats2)).

:- declare(darwin,assocOne('human',hasMother,'woman')).

:- update_assoc_stats(hasMother,darwin),
   assoc_stats(hasMother,darwin,Stats1,Stats2),
   write2ln((hasMother,darwin):(Stats1,Stats2)).


%% ------------------------------------------------------------
%% Constraint search
%% ------------------------------------------------------------

%%
%% 4 queens
%%

% variables and domains

domain(queens,V,[1,2,3,4])
:- member(V,[q1,q2,q3,q4]).


% constraint

no_attack(V1,X1,V2,X2)
:- X1 \= X2,
   atom_chars(V1,[_|L1]), number_string(R1,L1),
   atom_chars(V2,[_|L2]), number_string(R2,L2),
   abs(R1-R2) =\= abs(X1-X2).

% constraint graph

has_constraint(queens,(V1,V2),no_attack)
:- domain(queens,V1,_),
   domain(queens,V2,_),
   V1 \= V2.

:- search_all(queens,Solutions), write2ln(Solutions).

%% 
%% Map coloring
%% 

domain(mapa_a,V,[red,blue,green])
:- member(V,[a,b,c,d,e]).

has_constraint(mapa_a,(V1,V2),different_color)
:- SomeEdges = [ (a,b), (b,c), (c,d), (d,a) ],
   ( member((V1,V2),SomeEdges); member((V2,V1),SomeEdges) ).

has_constraint(mapa_a,(V1,V2),different_color)
:- ( V1=e, member(V2,[a,b,c,d]);
     V2=e, member(V1,[a,b,c,d]) ).

different_color(_,C1,_,C2)
:- C1 \= C2.
 
:- search_all(mapa_a,Solutions), write2ln(Solutions).

%%
%% TWO+TWO=FOUR
%%

% variables and domains

variables(twoplustwo,[t,w,o,f,u,r]).

tuple_variables(twoplustwo,[orx1,wx1ux2,tx2of]).

domain(twoplustwo,V,[0,1,2,3,4,5,6,7,8,9])
:- variables(twoplustwo,LV), member(V,LV), V\=f.
domain(twoplustwo,V,[0,1])
:- member(V,[f,x1,x2]).
domain(twoplustwo,orx1,Domain)
:- domain(twoplustwo,o,Do),
   domain(twoplustwo,r,Dr),
   domain(twoplustwo,x1,Dx1),
   cartesian_product([[]],Do,Po),
   cartesian_product(Po,Dr,Pr),
   cartesian_product(Pr,Dx1,Px1),
   findall(Elem,( member(Elem,Px1), [O,R,X1] = Elem,
                  2*O=:=R+10*X1 ), Domain).
domain(twoplustwo,wx1ux2,Domain)
:- domain(twoplustwo,w,Dw),
   domain(twoplustwo,x1,Dx1),
   domain(twoplustwo,u,Du),
   domain(twoplustwo,x2,Dx2),
   cartesian_product([[]],Dw,Pw),
   cartesian_product(Pw,Dx1,Px1),
   cartesian_product(Px1,Du,Pu),
   cartesian_product(Pu,Dx2,Px2),
   findall(Elem,( member(Elem,Px2), [W,X1,U,X2] = Elem,
                  2*W+X1=:=U+10*X2 ), Domain).
domain(twoplustwo,tx2of,Domain)
:- domain(twoplustwo,t,Dt),
   domain(twoplustwo,x2,Dx2),
   domain(twoplustwo,o,Do),
   domain(twoplustwo,f,Df),
   cartesian_product([[]],Dt,Pt),
   cartesian_product(Pt,Dx2,Px2),
   cartesian_product(Px2,Do,Po),
   cartesian_product(Po,Df,Pf),
   findall(Elem,( member(Elem,Pf), [T,X2,O,F] = Elem,
                  2*T+X2=:=O+10*F ), Domain).

cartesian_product(Prod0,Set,Prod)
:- findall(P,( member(T,Prod0), member(X,Set), append(T,[X],P) ),Prod).


% constraints

different_digit(_,X1,_,X2)
:- X1\=X2.

tuple_constraint0(_,[H1|_],_,X2)
:- H1==X2.
tuple_constraint0(_,X1,_,[H2|_])
:- X1==H2.
tuple_constraint1(_,[_,H1|_],_,X2)
:- H1==X2.
tuple_constraint1(_,X1,_,[_,H2|_])
:- X1==H2.
tuple_constraint2(_,[_,_,H1|_],_,X2)
:- H1==X2.
tuple_constraint2(_,X1,_,[_,_,H2|_])
:- X1==H2.
tuple_constraint3(_,[_,_,_,H1|_],_,X2)
:- H1==X2.
tuple_constraint3(_,X1,_,[_,_,_,H2|_])
:- X1==H2.

% constraint graph

has_constraint(twoplustwo,(V1,V2),different_digit)
:- variables(twoplustwo,Variables),
   member(V1,Variables), member(V2,Variables),
   V1 \= V2.

has_constraint(twoplustwo,(orx1,o),tuple_constraint0).
has_constraint(twoplustwo,(orx1,r),tuple_constraint1).
has_constraint(twoplustwo,(orx1,x1),tuple_constraint2).

has_constraint(twoplustwo,(wx1ux2,w),tuple_constraint0).
has_constraint(twoplustwo,(wx1ux2,x1),tuple_constraint1).
has_constraint(twoplustwo,(wx1ux2,u),tuple_constraint2).
has_constraint(twoplustwo,(wx1ux2,x2),tuple_constraint3).

has_constraint(twoplustwo,(tx2of,t),tuple_constraint0).
has_constraint(twoplustwo,(tx2of,x2),tuple_constraint1).
has_constraint(twoplustwo,(tx2of,o),tuple_constraint2).
has_constraint(twoplustwo,(tx2of,f),tuple_constraint3).

has_constraint(twoplustwo,(V,TV),Constraint)
:- variables(twoplustwo,Vars),
   member(V,[x1,x2|Vars]),
   tuple_variables(twoplustwo,TupleVars),
   member(TV,TupleVars),
   has_constraint(twoplustwo,(TV,V),Constraint).

:- search_all(twoplustwo,Solutions), 
   variables(twoplustwo,Vars),
   findall(S,( member(Full,Solutions),
               findall((Var,Val), ( member(Var,Vars), member((Var,Val),Full)), S),
               writeln(S) ),List),
   length(List,Len),
   writeln('Number of solutions':Len).

