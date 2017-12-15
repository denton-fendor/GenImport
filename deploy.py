#*===================================================================
#*
#* Licensed Materials - Property of IBM
#* IBM PureApplication System (5725-G32) for x86
#* IBM PureApplication System (5725-F46) for POWER
#* Copyright IBM Corporation 2009, 2014. All Rights Reserved.
#* US Government Users Restricted Rights - Use, duplication or disclosure
#* restricted by GSA ADP Schedule Contract with IBM Corp.
#*
#*===================================================================

import time
import os
import sys
import commands
import shutil
import string
import random

def id_generator(size=8,chars=string.ascii_letters+string.digits):
  return ''.join(random.choice(chars) for _ in range(size))

if ( len(sys.argv) < 3 ):
	print "usage : deployPattern.py deploy.properties"
	sys.exit()
else:
	whvPropFile=sys.argv[1]
	environment=sys.argv[2]
deployOption=dict()
createParms=dict()
parms = dict()
webList={"Production":"PROD-WEB - 1940",
	"Performance":"SYSPERF-WEB",
	"UAT":"PROD-UAT-WEB - 1943",
	"Data-Conversion":"PROD-DCON-WEB - 1946"}
appList={"Production":"PROD-APP - 1941",
	"Performance":"SYSPERF-APP - 1950",
	"UAT":"PROD-UAT-APP - 1944",
	"Data-Conversion":"PROD-DCON-APP - 1947"}
dbList={"Production":"PROD-APP - 1941",
	"Performance":"SYSPERF-DATA - 1951",
	"UAT":"PROD-UAT-DATA - 1945",
	"Data-Conversion":"PROD-DCON-DATA - 1948"}

ipWeb=webList[environment]
ipApp=appList[environment]
ipDB=dbList[environment]

print "Using property file : %s" % whvPropFile
try:
    f = open(whvPropFile)
    for line in f:
        try:
            key, value = line.split('=',1)
            parms[key] = value.replace('\n', '').strip()
        except:
            # No value on this line, do nothing
            e = line
    f.close()
except:
        print "Error: Can't open %s" % whvPropFile
#
# Get the deploy pattern name
#
deploymentName=parms['deploymentName']
del parms['deploymentName']
#
# select pattern to deploy then remove it from the list leaving only pattern parms
#
patternID = parms['pattern_id'].strip()
del parms['pattern_id']
pattern = None
print "Pattern id=%s" % patternID
try:
  pattern=deployer.virtualsystempatterns.get(patternID)
except IOError, e:
  print "Pattern does not exists or you do not have permission to the pattern"
  print e
  sys.exit(-1)
 
print "Pattern name=%s %s" % (pattern.app_name,pattern.patternversion)
#
# Get IP groups for the different tiers
#
webList=parms['web'].split(',')
appList=parms['app'].split(',')
dbList=parms['db'].split(',')

del parms['web']
del parms['app']
del parms['db']
webList
ipWeb='PROD-DCON-WEB - 1946'
#ipWeb='PROD-WEB - 1940'
ipApp='PROD-DCON-APP - 1947'
#ipApp='PROD-APP - 1941'
ipDB='PROD-DCON-DATA - 1948'
#ipDB='PROD-DATA - 1942'
#
# Select cloud group
#
cloud=deployer.clouds.list()[0]
deployOption['cloud_group'] = cloud
#
# Select env profile
#
profile=deployer.environmentprofiles.list({'name':environment})[0]
deployOption['environment_profile']=profile

# select a start time

ctime=time.strftime("%H%M%S")

# select an end time
#endtime = inputOrQuit('number of seconds until stop (default=no scheduled stop), or q to quit: ')
#if endtime:
#    createParms['endtime'] = time.time() + long(endtime)
if environment == "Production":
  keysize=10
else:
  keysize=5
for key in parms:
        upperKey=key.upper()
        if (upperKey.endswith('PASSWORD')):
                try:
                        rnd_key=parms[key] % id_generator(keysize) 
                        createParms[key]=rnd_key
                        print "%s = %s" % (key,rnd_key)
                except TypeError:
                        createParms[key]=parms[key]
                        print "%s = %s" % (key,parms[key])

        else:
                createParms[key]=parms[key]
                print "%s = %s" % (key,parms[key])
#list=pattern.listConfig()
deployOption['placement_only']=True
dep_name="%s v%s %s" % (deploymentName,pattern.patternversion,ctime)
virtualInstance=pattern.deploy(dep_name,deployOption,None,createParms)
p=virtualInstance.getPlacement()

placementList=p['vm-templates']
for i in range(len(p['vm-templates'])):
	nodeName=p['vm-templates'][i]['name']
	if nodeName in webList:
		instWeb=1L
	else:
		instWeb=0L
	if nodeName in appList:
		instApp=1L
	else:
		instApp=0L
	if nodeName in dbList:
		instDb=1L
	else:
		instDb=0L	
	print (nodeName,instWeb,instApp,instDb)
	for j in range(len(p['vm-templates'][i]['locations'][0]['cloud_groups'][0]['instances'])):
		for k in range(len(p['vm-templates'][i]['locations'][0]['cloud_groups'][0]['instances'][j]['nics'][0]['ip_groups'])):
        		ip=p['vm-templates'][i]['locations'][0]['cloud_groups'][0]['instances'][j]['nics'][0]['ip_groups'][k]['name']
			if ip == ipWeb:
        			p['vm-templates'][i]['locations'][0]['cloud_groups'][0]['instances'][j]['nics'][0]['ip_groups'][k]['new_instances']=instWeb
			if ip == ipApp:
        			p['vm-templates'][i]['locations'][0]['cloud_groups'][0]['instances'][j]['nics'][0]['ip_groups'][k]['new_instances']=instApp
			if ip == ipDB:
        			p['vm-templates'][i]['locations'][0]['cloud_groups'][0]['instances'][j]['nics'][0]['ip_groups'][k]['new_instances']=instDb
		
virtualInstance.deployPlacement({'placement':p})

print virtualInstance.deployment_name
print "virtualInstanceID=%s" % virtualInstance.id
virtualInstanceID=virtualInstance.id
time.sleep(120)
#get instance
instances=deployer.virtualsysteminstances.list({'id':virtualInstanceID})
if len(instances)==0:
  print "Instance %s does not exist." % (virtualInstanceID)
else:
  instance=instances[0]
  #print deployment history
  history=instance.history
  #for line in history:
    #print "%s: %s" % (line['created_time'],line['current_message'])
  name=instance.deployment_name
  status=instance.status
  print 'Instance "%s"... %s' % (name,status)
  if (status=="RUNNING") or  (status=="LAUNCHING"):
    #list virtual machines
    print 'Virtual machines:'
    virtualmachines=instance.virtualmachines
    for vm in virtualmachines:
      name=vm.displayname
      ip=vm.ip
      hostname=ip.userhostname
      ipaddr=ip.ipaddress
      print "  %s (%s): %s" % (hostname,ipaddr,name)

