import csv
import random
import string
import sys

#write a dirty version of the inputted filename to tmpfile,
#where the column indicated by colnum is made dirty
def writeDV(filename, tmpfile, colnum):
  with open(tmpfile, 'w+') as tmp:
    with open(filename, 'rb') as csvfile:
      csvreader = csv.reader(csvfile, delimiter=',')
      for i,row in enumerate(csvreader):
        if i == 0:
          continue
        else:
          csvwriter = csv.writer(tmp,delimiter=',',quotechar='"',quoting=csv.QUOTE_MINIMAL)
          dStr = perturb(row[colnum])
          row[colnum] = dStr
          csvwriter.writerow(row)

#describes different ways we might perturb a string
def perturb(s):
  DorC = random.randint(0,1)
  if DorC == 0:
    return s
  else:
    ptype = random.randint(0,2)
    if ptype == 0: #modify a suffix of the string
      ssize = random.randint(0,len(s)-2)
      prefix = s[:ssize]
      for i in range(len(s) - ssize):
        c = random.choice(string.ascii_letters)
        prefix = prefix + c
      return prefix
    elif ptype == 1: #append something to the end of the string
      suflen = random.randint(0,len(s)-1)
      suffix = ''
      for i in range(suflen):
        c = random.choice(string.ascii_letters)
        suffix = suffix + c
      return s + suffix
    elif ptype == 2: #delete something from the end of the string
      preflen = random.randint(1,len(s))
      return s[:preflen] 

#pick a random sample of a given size from the given list of values from a column of a dataset
def pickSample(ffull,size):
  res = dict()
  indices = random.sample(range(len(ffull)),size)
  for i,l in enumerate(ffull):
    if i in indices:
      res[i] = l
  return res    

#return an array of the given column from the ground truth file
def parseF(filename,header,colnum):
  res = list()
  with open(filename, 'r') as fh:
    csvreader = csv.reader(fh, delimiter=',')
    for i,row in enumerate(csvreader):
      if header and i == 0:
        continue
      res.append(row[colnum])
  return res
  

#given a sample of records in the form of a dictionary of file line numbers to arrays of strings,
#and the g_truth as an array in the same order as the dictionary,
#determine whether the strings match. If they do not, then fix the strings in the dictionary
#and add incorrect string --> correct string to the result dictionary. Return this result dictionary
#after going over the sample dictionary
def f_clean(sample,g_truth):
  res = dict()
  for key in sample:
    errstr = sample[key]
    truestr = g_truth[key]
    if truestr != errstr:
      res[errstr] = truestr 
  return res

#find the total number of errors in the dirty dataset
def numErrors(darr,gt):
  res = 0
  for i,g in enumerate(gt):
    if darr[i] != g:
      res = res + 1
  return res
  

#measure the empirical accuracy of the given mapping on the full dataset
def empAcc(mapping,ffull,gt):
  denom = numErrors(ffull,gt)
  ccnt = 0
  for e in ffull:
    value = mapping.get(e)
    if value != None:
      ccnt = ccnt + 1
  acc = float(ccnt) / float(denom)
  return acc 

#Finds and displays the results for percentage of errors remaining in testing set after using
#empirical accuracy, cross-validation, and species estimation approaches
def main():
  #first argument: input file
  #second argument: desired name of dirty file
  #third argument: column number to perturb
  ofile = sys.argv[1]
  dfile = sys.argv[2]
  cnum = int(sys.argv[3])
  writeDV(ofile,dfile,cnum)
  gtarr = parseF(ofile,True,cnum)
  darr = parseF(dfile,False,cnum)
  sample = pickSample(darr, len(gtarr)/8) 
  newrules = f_clean(sample,gtarr)
  eA = empAcc(newrules,darr,gtarr)
  print(eA)
     
main()
