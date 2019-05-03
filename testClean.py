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

#find the number of errors in the given sample of the dirty dataset
def numES(sample,gt):
  res = 0
  for i in sample:
    if sample[i] != gt[i]:
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

#partition given array, darr, into pnum parts
def partition(darr,pnum):
  res = list()
  psize = len(darr) / pnum
  tmp = dict()
  scnt = 0 #size count
  pcnt = 0 #part count
  for i,l in enumerate(darr):
    tmp[i] = l
    scnt = scnt + 1
    if scnt >= psize and pcnt != pnum:
      dn = tmp.copy()
      res.append(dn)
      tmp = dict()
      pcnt = pcnt + 1
      scnt = 0
    elif scnt >= psize and pcnt == pnum:
      if i == len(darr) - 1:
        dn = tmp.copy()
        res.append(dn)

  return res
        
#measure the accuracy of a map in identifying errors
#in a sample, as opposed to the entire dataset
def hAcc(mapping,sample,gt):
  ccnt = 0
  denom = numES(sample,gt)
  for key in sample:
    dstr = sample[key]
    value = mapping.get(dstr)
    if value != None:
      ccnt = ccnt + 1
  res = float(ccnt) / float(denom)
  return res

#measure the accuracy of a map built using cross-validation
def crossVal(darr,pnum,gtarr):
  parts = partition(darr,pnum) 
  mapping = dict()
  avg = 0.0
  for i,holdout in enumerate(parts):
    for j,p in enumerate(parts):
      if j == i:
        continue
      newrules = f_clean(p,gtarr)
      mapping.update(newrules)
    #use the mapping here, and then set it back to dict() 
    acc = hAcc(newrules,holdout,gtarr)
    avg = avg + acc
  res = avg / float(len(parts))
  return res

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
  sample = pickSample(darr, len(gtarr)/2) 
  newrules = f_clean(sample,gtarr)
  
  #Empirical Accuracy
  eA = empAcc(newrules,darr,gtarr)
  print(eA)

  #Cross-Validation
  cV = crossVal(darr,2,gtarr)
  print(cV)
       

main()
