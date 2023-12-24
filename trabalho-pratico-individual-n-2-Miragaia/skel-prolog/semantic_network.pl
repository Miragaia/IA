
declare(User,subtype(Sub,Super))
:- isTypeName(Sub), isTypeName(Super),
   retractall(declared(User,subtype(Sub,_))),
   assert(declared(User,subtype(Sub,Super))).

declare(User,member(Obj,Type))
:- isObjectName(Obj), isTypeName(Type),
   retractall(declared(User,member(Obj,_))),
   assert(declared(User,member(Obj,Type))).

declare(User,assocOne(E1,Assoc,E2))
:- retractall(declared(User,assocOne(E1,Assoc,_))),
   assert(declared(User,assocOne(E1,Assoc,E2))).

declare(User,association(E1,Assoc,E2))
:- % writeln(b), 
   retract(declared(User,association(E1,Assoc,Entities))), !,
   assert(declared(User,association(E1,Assoc,[E2|Entities]))).

declare(User,association(E1,Assoc,E2))
:- assert(declared(User,association(E1,Assoc,[E2]))).

%

isTypeName(Name)
:- atom_chars(Name,[H|_]), char_type(H,lower).

isObjectName(Name)
:- atom_chars(Name,[H|_]), char_type(H,upper).

