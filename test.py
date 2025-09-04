class A:
    a = 1
    
class B:
    a = 2
    
    
class C:
    a = 1


abc = 555
test = 5
    
if abc == 3:
    ...
elif any(i.a == test for i in (A, B, C)):
    print("a из классов рвна test")