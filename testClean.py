import csv
import random
import string
import sys
import Levenshtein as pL

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
#after going over the sample dictionary and correcting the sample of the dirty dataset based on it.
def f_clean(sample,darr,g_truth):
  res = dict()
  ecnt = 0
  for key in sample:
    errstr = sample[key]
    truestr = g_truth[key]
    if truestr != errstr:
      ecnt = ecnt + 1
      res[errstr] = truestr 
      darr[key] = truestr
  #print("Number of Errors in Sample: " + str(ecnt))
  return res

#given a sample of records in the same form as described in f_clean,
#and g_truth, pretend we do not know the position of the dirty string in the ground truth.
#Then, find the string in the ground truth with the minimum Levenshtein distance from the dirty string.
#Add this rule to the result
#Return the resulting map
def f_cleanv2(sample,darr,g_truth,thresh):
  res = dict()
  ecnt = 0
  for key in sample:
    errstr = sample[key]
    cnlst = list()
    mindist = sys.maxint
    minInd = 0
    for i,s in enumerate(g_truth):
      dst = pL.distance(errstr,s)
      if dst <= thresh:
        cnlst.append(s)
      elif dst < mindist:
        mindist = dst
        minInd = i
    truestr = None
    if len(cnlst) == 0:
      truestr = g_truth[minInd]
    else:
      truestr = random.choice(cnlst)
    if truestr != errstr:
      ecnt = ecnt + 1
      res[errstr] = truestr
      darr[key] = truestr

  return res
      


#find the total number of errors in the dirty dataset
def numErrors(darr,gt):
  res = 0
  for i,g in enumerate(gt):
    if darr[i] != g:
      res = res + 1
  return res

#find the number of clean records in the dirty dataset
def numClean(darr,gt):
  res = 0
  for i,g in enumerate(gt):
    if darr[i] == g:
      res = res + 1
  return res

#find the number of errors in the given sample of the dirty dataset
def numES(sample,gt):
  res = 0
  for i in sample:
    if sample[i] != gt[i]:
      res = res + 1
  return res
  
#find the number of clean records in the given sample of the dirty dataset
def numCS(sample,gt):
  res = 0
  for i in sample: 
    if sample[i] == gt[i]:
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
  #print("Empirical Accuracy")
  #print("Number of Errors Fixed: " + str(ccnt))
  #print("Total Number of Errors: " + str(denom))
  acc = float(ccnt) / float(denom)
  return acc 

#measure the empirical accuracy of the given the mapping on the full dataset,
#which is prone to false positives
#Also, we simply stop when we find the first string in the sample that matches close enough,
#instead of finding them all and then randomly breaking ties. That could affect our results later.
def empAccFP(mapping,ffull,gt,thresh):
  denom = numErrors(ffull,gt)
  ccnt = 0
  for e in ffull:
    d = False
    for key in mapping:
      if d == True:
        break
      elif pL.distance(key,e) <= thresh:
        ccnt = ccnt + 1 
        d = True
  #print("Empirical Accuracy")
  #print("Number of Errors Fixed: " + str(ccnt))
  #print("Total Number of Errors: " + str(denom))
  acc = float(ccnt) / float(denom)
  return acc 

#measure the false transformation rate of the given mapping on the full dataset
def empFP(mapping,ffull,gt,thresh):
  denom = numClean(ffull,gt)
  ccnt = 0
  for i,e in enumerate(ffull):
    d = False
    for key in mapping:
      if d == True:
        break
      elif pL.distance(key,e) <= thresh and ffull[i] == gt[i]:
        ccnt = ccnt + 1
        d = True
  fts = float(ccnt) / float(denom)
  return fts
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
#except now, the cleaning function is prone to false positives
#Also, we simply stop when we find the first string in the sample that matches close enough,
#instead of finding them all and then randomly breaking ties. That could affect our results later.
def hAccFP(mapping,sample,gt,thresh):
  ccnt = 0
  denom = numES(sample,gt)
  for key in sample:
    dstr = sample[key]
    d = False
    for value in mapping:
      if d == True:
        break
      elif pL.distance(dstr,value) <= thresh:
        ccnt = ccnt + 1
        d = True
  #print("Number of Errors Fixed: " + str(ccnt))
  #print("Total Number of Errors: " + str(denom))
  res = float(ccnt) / float(denom)
  return res

#measure the false positive rate of a map in identifying errors
#in a sample, as opposed to the entire dataset
def hFP(mapping,sample,gt,thresh):
  ccnt = 0
  denom = numCS(sample,gt)
  for key in sample:
    dstr = sample[key]
    d = False
    for value in mapping:
      if d == True:
        break
      elif pL.distance(dstr,value) <= thresh and dstr == gt[key]:
        ccnt = ccnt + 1
        d = True
  res = float(ccnt) / float(denom)
  return res

#measure the accuracy of a map in identifying errors
#in a sample, as opposed to the entire dataset
#Note: here, thresh is an unused variable
def hAcc(mapping,sample,gt,thresh):
  ccnt = 0
  denom = numES(sample,gt)
  for key in sample:
    dstr = sample[key]
    value = mapping.get(dstr)
    if value != None:
      ccnt = ccnt + 1
  #print("Number of Errors Fixed: " + str(ccnt))
  #print("Total Number of Errors: " + str(denom))
  res = float(ccnt) / float(denom)
  return res

#measure the accuracy of a map built using cross-validation
def crossVal(darr,pnum,gtarr,thresh,hAcc):
  parts = partition(darr,pnum) 
  mapping = dict()
  avg = 0.0
  for i,holdout in enumerate(parts):
    dtmp = list()
    dtmp[:] = darr
    for j,p in enumerate(parts):
      if j == i:
        continue
      newrules = f_clean(p,dtmp,gtarr)
      mapping.update(newrules)
    #use the mapping here, and then set it back to dict() 
    #print("Holdout: " + str(i))
    acc = hAcc(newrules,holdout,gtarr,thresh)
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
  thresh = 10
  gtarr = parseF(ofile,True,cnum)
  darr = parseF(dfile,False,cnum)
  darr2 = list()
  darr2[:] = darr
  sample = pickSample(darr, len(gtarr)/8) 
  newrules = f_clean(sample,darr,gtarr)
  
  #Empirical Accuracy
  eA = empAcc(newrules,darr,gtarr)

  #Cross-Validation
  cV = crossVal(darr2,8,gtarr,thresh,hAcc)

  print("Building a table from Sample and Ground Truth using Exact Match (and Position)")
  print("Empirical Accuracy- percentage of errors detected: " + str(eA))
  print("Cross-Validation- percentage of errors detected: " + str(cV))

  gtarrv2 = parseF(ofile,True,cnum)
  darrv2 = parseF(dfile,False,cnum)
  darr3 = list()
  darr3[:] = darr
  sample = pickSample(darrv2, len(gtarrv2)/8) 
  newrules = f_clean(sample,darrv2,gtarrv2)
  
  #Empirical Accuracy but with a cleaning function that exhibits false positives
  eA = empAccFP(newrules,darrv2,gtarrv2,thresh)

  #Cross-Validation, but with a cleaning function that exhibits false positives
  cV = crossVal(darr3,8,gtarrv2,thresh,hAccFP)
  
  print("Building a table from Sample and Ground Truth using Edit Distance")
  print("Empirical Accuracy- percentage of errors detected: " + str(eA))
  print("Cross-Validation- percentage of errors detected: " + str(cV))

  gtarrv3 = parseF(ofile,True,cnum)
  darrv3 = parseF(dfile,False,cnum)
  darr4 = list()
  darr4[:] = darr
  sample = pickSample(darrv3, len(gtarrv3)/8) 
  newrules = f_clean(sample,darrv3,gtarrv3)
  #Empirical False positives
  eA = empFP(newrules,darrv3,gtarrv3,thresh)

  #Cross-Validation, but with a cleaning function that exhibits false positives
  cV = crossVal(darr4,8,gtarrv3,thresh,hFP)
  print("Measuring False Positive Rate")
  print("Empirical False Positive Rate: " + str(eA))
  print("Cross-Validation False Positive Rate: " + str(cV))
  
       

main()
