class Test:

    def a():
        total = 100
        new_total = Test.b(total)
        new_total = Test.c(new_total)
        print(new_total)

    def b(total):
        total -= 40
        return total

    def c(total):
        total -= 30
        return total

Test.a()