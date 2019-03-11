from django.test import TestCase

# Create your tests here.

dict = {
    'a':1,
    'b':2,
    'c':3
}
print(dict.keys())#dict_keys(['a', 'b', 'c'])
print(dict.values())#dict_values([1, 2, 3])
print(dict.items())#dict_items([('a', 1), ('b', 2), ('c', 3)])
print(dict.__str__())#{'a': 1, 'b': 2, 'c': 3}
print(dict)#{'a': 1, 'b': 2, 'c': 3}
print(dict.keys().__dir__())
print(dict.keys().__iter__())
print(dict.__class__)
print(dict.update({'d':4}))
print(dict.update({'b':3}))
print(dict)

groups_name_list = ['a','1','b','c']
print('|'.join(groups_name_list))#a|b|c