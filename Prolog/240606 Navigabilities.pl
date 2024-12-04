% This is a small attempt to represent network navigabilities as modeled in RSM (RailSystemModel; see rsm.uic.org) and test their behaviour using PROLOG.

% PROLOG in a nutshell: P(...) is a unary predicated, Q(..., ...) a binary predicate, etc.
% Variables have an initial capital ("X"), while constants have an initial lower case letter ("a1").
% A :- B means "if B, then A" or "A if B" (sufficient condition).
% Logical operators are "," (AND) and ";" (inclusive OR).
% \+ A means "A cannot be proven true" which results in "A is false", as PROLOG assumes that failure to prove entails negation ("negation as failure").
% The latter feature is a frequent source of misinterpretations. I got into that trap more than once. You've been warned.

% Net elements:
% This is a simple network composed of 4 linear elements (track sections) a, b, c, d.
% Imagine a on the left, d on the right, b and c in parallel in the middle connecting to a and d with switches at both ends
% Switches are no track topology elements; their presence materializes into navigabilities, i.e. binary predicates.

linearelement(a) .
linearelement(b) .
linearelement(c) .
linearelement(d) .

% ... and a loop at the end of d:
linearelement(e) .

netelement(X) :- linearelement(X) .

% Ports definitions: each linear element N has two ports (= extremities), conventionally names N0 and N1
port(a0, a) .
port(a1, a) .
port(b0, b) .
port(b1, b) .
port(c0, c) .
port(c1, c) .
port(d0, d) .
port(d1, d) .

% a loop has two coinciding ports (having  single port instead would not allow to describe running rolling stock behaviour properly)
port(e0, e) .
port(e1, e) .

% Connection definitions: this tells how elements are assembled.
% Connection is a relation between ports. Remember however that PROLOG has no types, and we do not check.
:- table connectedTo/2 .  % this directive prevents infinite loops
% Connections are symmetric:

% Connection assertions: these define the topology layout
connectedTo(a1, b0) .
connectedTo(a1, c0) .
connectedTo(b1, d0) .
connectedTo(c1, d0) .
connectedTo(d1, e0) .
connectedTo(d1, e1) .  % Which, together with the above, defines a loop indeed.
% Note: we do not assert connectedTo(a0, a1) etc.; while it seems obvious that ports at extremities of a linear element "are connected" (by the piece of track between them), this is not a general case when defining non-linear elements (multiport objects).
% Port connection ONLY tells about how track sections are assembled with OTHER track sections.

connectedTo(X,Y) :- connectedTo(Y,X).
% Connections are transitive:
connectedTo(X,Y) :- connectedTo(X,Z), connectedTo(Z,Y).
% consequently, when three track sections are connected in one "point" (case of a switch), it is enough to assert two connections and the third one will be inferred.


% Navigability definitions
% Navigability is a relation between ports. It is directed (hence navigableTo, and its reciprocal property navigableFrom).
% Navigability is express "end to end", from the port used when exiting a [linear] element to the port used when exiting the other [linear] element.
% This orientation is a necessary condition to be able to reason on navigability and use transitivity to find paths between any pair of linear elements.

:- table navigableToTransitive/2 . % this directive prevents infinite loops

% navigableTo is not symmetric! think of sprung switches...
% Note: in PROLOG, ',' means 'AND' (logical conjunction) and ';' means 'OR' (logical disjunction).
navigableToTransitive(X,Y) :- navigableTo(X, Y).
navigableToTransitive(X, Y) :- navigableToTransitive(X,Z), navigableTo(Z,Y).

% Navigability assertions:
navigableTo(a1, b1) .
navigableTo(b0, a0) .

navigableTo(a1, c1) .
navigableTo(c0, a0) .

navigableTo(b1, d1) .
navigableTo(d0, b0) .

navigableTo(c1, d1) .
navigableTo(d0, c0) .

% element e is a loop with entry on port e0 and exit on e1 (using a sprung switch): single running direction.
% Deactivate it by commenting it out, if needed.
navigableTo(d1, e1) .
navigableTo(e1, d0) .  % not e0 !

% Reverse navigability
:- table navigableFrom/2 .
navigableFrom(X, Y) :- navigableTo(Y, X) .

% Non-navigability
% REMINDER: in PROLOG, there is no actual negation; "\+" means "not proven" which is assimilated with "false".
% Caveat: in other words, PROLOG rests on a closed-world assumption, which is different from ontology open world assumption (what cannot be proven true is not false, but merely unknown). Take great care.
nonNavigableTo(X, Y) :- \+ navigableTo(X,Y) .

% The "intuitive" assertion above will yield counter-intuitive results when using variables in a query.
% For instance, nonNavigableTo(b1, c0) and nonNavigableTo(b1, c1) will correctly be evaluated to true.
% However, nonNavigableTo(b1, X) for instance evaluates to false, because there is at lease one navigable path leading to some X, making navigableTo(b1, X) true.

% European Railway Agency-style navigability (expressed between net elements, regardless of ports)
% Again, PROLOG is untyped, so use with precaution. Here, we explicitly check the types of X and Y (must be elements!) and A and B (must be ports!) although it is not necessary.
:- table navigable/2 .
navigable(X,Y) :- netelement(X), netelement(Y), port(A,X), port(B,Y), navigableTo(A,B) .

% Note that navigable is not transitive even though it is inferred from navigableTo that is transitive.
% This is because the nodes involved (A and B) may vary.
% The queries yield correct results:
% - Without loop, navigable(b,c) evaluates to false.
% - With loop, navigable(b,c) evaluates to true.
% If however navigable(a, b) etc. were asserted, transitivity would yield contradictions,
% here: navigable(b,c) would always evaluate to true, even without any loop.

% Suggested queries:
%
% Find all navigabilities from port a1:
% navigableTo(a1, X) . % or, alternatively:
% navigableFrom(X, a1) .
% Check that there is no navigability from b to c:
% at port level, this will be evaluated to false:
% navigableTo(b1, c0) ; navigableTo(b1, c1) ; navigableTo(b0, c0) ; navigableTo(b0, c1) .
% Or, at net element level:
% navigable(b, c) .
% Activating the loop will change the results, as expected.

% Now, let us introduce (nominal) element lengths:

elementlength(a, 100) .
elementlength(b, 220) .  % the diverted track is supposedly a bit longer than the through track c, below
elementlength(c, 200) .
elementlength(d, 150) .
elementlength(e, 450) .

% sum_element_lengths(ListOfElements, SumOfLengths)
% This uses maplist to apply elementlength to each element and sum_list to sum up the lengths.
% Note: these functions may be SWI PROLOG-specific.
sum_element_lengths(Elements, TotalLength) :-
    maplist(elementlength, Elements, Lengths), % Apply elementlength/2 to each element
    sum_list(Lengths, TotalLength).            % Sum the resulting list of lengths

% find_path(Start port, End port, Path)
% A path is a list of ports starting from Start port and ending at End port.
find_path(Start, End, [Start, End]) :-
    navigableTo(Start, End).

find_path(Start, End, [Start|Rest]) :-
    navigableTo(Start, Next),
    Start \= End,
    find_path(Next, End, Rest).

elementlength_of_port(Port, Length) :-
    port(Port, Element),
    elementlength(Element, Length).

% path_length(Path, Length)
% Computes the total length of all elements in Path
path_length([], 0).
path_length([H|T], TotalLength) :-
    elementlength_of_port(H, Length),
    path_length(T, RestLength),
    TotalLength is Length + RestLength.

% find_shortest_path(Start, End, ShortestPath, MinLength)
% Finds the shortest path from Start to End
find_shortest_path(Start, End, ShortestPath, MinLength) :-
    findall(Path, find_path(Start, End, Path), Paths),
    maplist(path_length, Paths, Lengths),
    min_member(MinLength, Lengths),
    nth0(Index, Lengths, MinLength),  % Find the index of the shortest length
    nth0(Index, Paths, ShortestPath).  % Retrieve the corresponding path

% Query examples:
% navigableTo(a1, d1) returns false.
% navigableToTransitive(a1, d1) returns true.
% find_shortest_path(a1, d1, X, Y) returns X = [a1,c1,d1] and Y = 450.

