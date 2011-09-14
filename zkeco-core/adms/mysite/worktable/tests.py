"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.failUnlessEqual(1 + 1, 2)

__test__ = {"doctest": """
Another way to test that 1 + 1 is equal to 2.

>>> 1 + 1 == 2
True
"""}

def create_department(num=500):
    from mysite.personnel.models import Department
    import random
    dept_all=list(Department.objects.all())
    if len(dept_all)==0:
        d=Department(name="our company",parent=None)
        d.save()
        dept_all.append(d)
    for i in range(num):
        try:
            d=Department(name="department"+str(i),code="code"+str(i))
            d.parent=dept_all[int(random.random()*len(dept_all))]
            d.save()
            dept_all.append(d)
            #print 'ok %s'%i
        except:
            import traceback;traceback.print_exc()

def delete_deparment(num=500):
    from mysite.personnel.models import Department
    Department.objects.all().delete();
        