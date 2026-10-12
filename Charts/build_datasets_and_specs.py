import csv, json, re, io
U='/mnt/user-data/uploads/'; O='/mnt/user-data/outputs/vega/'
S="https://vega.github.io/schema/vega-lite/v5.json"
def rd(f,enc='utf-8-sig'): return list(csv.reader(open(U+f,encoding=enc,newline='')))
def num(x):
    x=str(x).replace(',','').replace('$','').strip()
    try: return float(x)
    except: return None
def ci(s):
    m=re.match(r'\s*([\d.]+)\D+([\d.]+)',s or ''); return (float(m[1]),float(m[2])) if m else (None,None)
def save(n,spec):
    d=spec.get('data',{})
    if 'values' in d:
        vals=d['values']; cn=n.replace('.vl.json','.csv')
        cols=list(dict.fromkeys(k for v in vals for k in v))
        w=csv.DictWriter(open(O+cn,'w',newline='',encoding='utf-8'),fieldnames=cols); w.writeheader(); w.writerows(vals)
        spec['data']={'url':cn,'format':{'type':'csv'}}
    json.dump(spec,open(O+n,'w'),indent=1,ensure_ascii=False); print(n)
cfg={"view":{"stroke":None},"axis":{"labelFontSize":11,"titleFontSize":12},"title":{"fontSize":15,"anchor":"start"}}

# 1 pyramid: BMI category by sex
r=rd('Gender-Rate.csv'); vals=[]
for row in r[2:]:
    for sex,i in (('Males',1),('Females',4)):
        lo,hi=ci(row[i+1]); vals.append({"bmi":row[0],"sex":sex,"pct":num(row[i]),"lo":lo,"hi":hi})
order=[r_[0] for r_ in r[2:]]
save('1_population_pyramid.vl.json',{"$schema":S,"config":cfg,"title":"Adult BMI distribution by sex (pyramid)","data":{"values":vals},
 "transform":[{"calculate":"datum.sex=='Males' ? -datum.pct : datum.pct","as":"signed"}],
 "encoding":{"y":{"field":"bmi","type":"ordinal","sort":order[::-1],"axis":{"title":None,"labelLimit":260}}},
 "layer":[{"mark":{"type":"bar","tooltip":True},"encoding":{"x":{"field":"signed","type":"quantitative","title":"% of adults (Males ← → Females)","scale":{"domain":[-50,45]},"axis":{"format":"~s","labelExpr":"abs(datum.value)+'%'"}},
   "color":{"field":"sex","type":"nominal","scale":{"domain":["Males","Females"],"range":["#2a6f97","#e07a5f"]},"legend":{"title":None,"orient":"top"}},
   "tooltip":[{"field":"bmi"},{"field":"sex"},{"field":"pct","title":"%"},{"field":"lo","title":"95% CI low"},{"field":"hi","title":"95% CI high"}]}},
  {"mark":{"type":"text","dx":0,"align":"center","fontSize":11},"encoding":{"x":{"field":"signed","type":"quantitative"},"text":{"field":"pct","format":".1f"},"xOffset":{"value":0},
   "color":{"value":"#333"}}}],"width":520,"height":260})
# fix label placement: text beyond bar end
sp=json.load(open(O+'1_population_pyramid.vl.json')); sp['data']={'values':vals}
sp['layer'][1]['mark']={"type":"text","fontSize":11,"align":{"expr":"datum.sex=='Males' ? 'right':'left'"},"dx":{"expr":"datum.sex=='Males' ? -4:4"}}
save('1_population_pyramid.vl.json',sp)

# 2 social determinants
r=rd('Social-Rate.csv'); years=['2007–08','2011–12','2014–15','2017–18']; grp=None; sd=[]; tm=[]
for row in r[4:]:
    if not row[0]: continue
    if all(c=='' for c in row[1:]): grp=row[0]; continue
    cat=re.sub(r'\([^)]*\)','',row[0]).strip()
    cat=(cat[:42]+'…') if len(cat)>43 else cat
    g=re.sub(r'\([a-z]\)','',grp).strip()
    for k,y in enumerate(years):
        b=1+6*k; lo,hi=ci(row[b+4])
        rec={"group":g,"category":cat,"year":y,"crude":num(row[b]),"asr":num(row[b+3]),"lo":lo,"hi":hi}
        if g in('Sex',) or cat=='Persons': tm.append(rec)
        if g!='Sex': sd.append(rec)
sd=[d for d in sd if d['group']!='Sex']
for d in sd: d['group']=d['group'].replace('(k)','').replace('(g)','').strip()
sd=[d for d in sd if not (d['group']=='Occupation' and d['category'] in('Unemployed','Not in labour force'))]
save('2_social_determinants.vl.json',{"$schema":S,"config":cfg,"title":"Obesity in adults 18–64 by social determinant (age-standardised %, 2007–08 vs 2017–18)",
 "data":{"values":sd},"transform":[{"filter":"datum.year=='2007–08' || datum.year=='2017–18'"}],
 "facet":{"row":{"field":"group","type":"nominal","title":None,"header":{"labelAngle":0,"labelAlign":"left","labelFontWeight":"bold"}}},
 "spec":{"width":420,"height":{"step":18},"encoding":{"y":{"field":"category","type":"nominal","sort":None,"title":None}},
  "layer":[{"mark":{"type":"rule","color":"#bbb"},"transform":[{"aggregate":[{"op":"min","field":"asr","as":"mn"},{"op":"max","field":"asr","as":"mx"}],"groupby":["category"]}],"encoding":{"x":{"field":"mn","type":"quantitative"},"x2":{"field":"mx"}}},
   {"mark":{"type":"point","filled":True,"size":70,"tooltip":True},"encoding":{"x":{"field":"asr","type":"quantitative","title":"Obese, age-standardised %","scale":{"zero":False}},
    "color":{"field":"year","type":"nominal","scale":{"range":["#9aa5b1","#c0392b"]},"legend":{"title":None,"orient":"top"}},
    "tooltip":[{"field":"category"},{"field":"year"},{"field":"asr","title":"Age-std %"},{"field":"crude","title":"Crude %"},{"field":"lo","title":"CI low"},{"field":"hi","title":"CI high"}]}}]},
 "resolve":{"scale":{"y":"independent"}}})

# 3 over time
t=[d for d in tm if d['category'] in('Males','Females','Persons')]
save('3_obesity_over_time.vl.json',{"$schema":S,"config":cfg,"title":"Obesity prevalence, adults 18–64, 2007–08 to 2017–18 (age-standardised %)","data":{"values":t},
 "encoding":{"x":{"field":"year","type":"ordinal","title":None,"axis":{"labelAngle":0}},
  "color":{"field":"category","type":"nominal","title":None,"scale":{"domain":["Males","Females","Persons"],"range":["#2a6f97","#e07a5f","#222"]}}},
 "layer":[{"mark":{"type":"errorband","opacity":0.15},"encoding":{"y":{"field":"lo","type":"quantitative","title":"% obese","scale":{"zero":False}},"y2":{"field":"hi"}}},
  {"mark":{"type":"line","point":True,"tooltip":True},"encoding":{"y":{"field":"asr","type":"quantitative"},"tooltip":[{"field":"category"},{"field":"year"},{"field":"asr","title":"Age-std %"},{"field":"lo"},{"field":"hi"}]}}],"width":520,"height":320})

# 4 map + ranked bar
CODES={g['properties']['Code'] for g in json.load(open(U+'PHA_2021_Aust_GDA2020_Gen50.json'))['objects']['PHA_2021_Aust_GDA2020_Gen50']['geometries']}
r=rd('PHIDU-Rate.csv','cp1252'); rows=[]; state=None
for row in r[5:]:
    if not row[0]: continue
    if not row[0].isdigit():
        state=row[0].title(); continue
    if len(row[0])<5 or int(row[0]) not in CODES: continue
    a=num(row[49]); n=num(row[48]); ow=num(row[40])
    lo,hi=num(row[50]),num(row[51])
    if any(x["Code"]==int(row[0]) for x in rows): continue
    rows.append({"Code":int(row[0]),"Name":row[1].strip(),"State":state,"obese_n":n,"obese_asr":a,"obese_lo":lo,"obese_hi":hi,"overweight_asr":ow})
w=csv.DictWriter(open(O+'phidu_obesity_clean.csv','w',newline='',encoding='utf-8'),fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
print(len(rows),sum(1 for x in rows if x['obese_asr'] is not None))
lk={"lookup":"properties.Code","from":{"data":{"url":"phidu_obesity_clean.csv"},"key":"Code","fields":["Name","State","obese_asr","obese_n"]}}
save('4_obesity_map_ranked_bar.vl.json',{"$schema":S,"config":cfg,"title":"Adult obesity by Population Health Area, 2022 (modelled ASR per 100)",
 "params":[{"name":"pick","select":{"type":"point","fields":["Name"],"on":"click"}}],
 "hconcat":[
  {"width":520,"height":460,"data":{"url":"PHA_2021_Aust_GDA2020_Gen50.json","format":{"type":"topojson","feature":"PHA_2021_Aust_GDA2020_Gen50"}},
   "projection":{"type":"mercator"},"transform":[lk],
   "mark":{"type":"geoshape","stroke":"#fff","strokeWidth":0.1,"invalid":None},
   "encoding":{"color":{"condition":{"test":"!isValid(datum.obese_asr)","value":"#e3e3e3"},"field":"obese_asr","type":"quantitative","title":"Obese ASR /100","scale":{"scheme":"orangered","domain":[10,45],"clamp":True},"legend":{"orient":"bottom"}},
    "opacity":{"condition":{"param":"pick","value":1},"value":0.85},
    "tooltip":[{"field":"Name","title":"PHA"},{"field":"State"},{"field":"obese_asr","title":"ASR per 100"},{"field":"obese_n","title":"Estimated number","format":","}]}},
  {"width":260,"height":{"step":14},"data":{"url":"phidu_obesity_clean.csv"},
   "transform":[{"filter":"isValid(datum.obese_asr)"},{"window":[{"op":"rank","as":"rank"}],"sort":[{"field":"obese_asr","order":"descending"}]},{"filter":"datum.rank<=25"}],
   "title":"Top 25 PHAs by obesity rate","mark":{"type":"bar","tooltip":True,"color":"#c0392b"},
   "encoding":{"y":{"field":"Name","type":"nominal","sort":"-x","title":None,"axis":{"labelLimit":220}},"x":{"field":"obese_asr","type":"quantitative","title":"ASR per 100"},
    "opacity":{"condition":{"param":"pick","value":1},"value":0.6},
    "tooltip":[{"field":"Name"},{"field":"State"},{"field":"obese_asr","title":"ASR per 100"}]}}]})

# 5 comorbidities
r=rd('ComorbidityCount.csv'); co=[]
for row in r[1:]:
    co.append({"code":row[0],"diagnosis":row[1].strip(),"with_obesity":num(row[2]),"pct_of_obesity_separations":num(row[4]),"total_separations":num(row[5])})
save('5_comorbidities.vl.json',{"$schema":S,"config":cfg,"title":"Top 20 principal diagnoses among hospital separations with obesity (U78.1) coded","data":{"values":co},
 "width":480,"height":{"step":20},"mark":{"type":"bar","color":"#6a4c93","tooltip":True},
 "encoding":{"y":{"field":"diagnosis","type":"nominal","sort":"-x","title":None,"axis":{"labelLimit":340}},"x":{"field":"with_obesity","type":"quantitative","title":"Separations with U78.1 code"},
  "tooltip":[{"field":"code"},{"field":"diagnosis"},{"field":"with_obesity","format":",","title":"With obesity"},{"field":"pct_of_obesity_separations","title":"% of all U78.1 separations"}]}})

# 6 limitations
r=rd('issue-Rate.csv'); li=[]; sex=None
meas=[('Obesity',4),('Severe obesity',10),('Abdominal obesity',13)]
for row in r[4:]:
    if row[1:] and row[0]=='' and row[1] in('Males','Females','Persons'): sex=row[1]; continue
    if not row[0] or sex=='Persons' : continue
    for m,i in meas:
        lo,hi=ci(row[i+1]); li.append({"sex":sex,"severity":row[0],"measure":m,"pct":num(row[i]),"lo":lo,"hi":hi})
sev=['Has core limitations','Profound','Severe','Moderate','Mild','Schooling/employment restriction only','Does not have core limitations','No limitation or specific restriction','No disability']
save('6_limitations.vl.json',{"$schema":S,"config":cfg,"title":"Obesity by severity of core limitations and sex, adults 2022","data":{"values":li},
 "facet":{"column":{"field":"measure","type":"nominal","title":None,"sort":["Obesity","Severe obesity","Abdominal obesity"]}},
 "spec":{"width":230,"height":300,"encoding":{"y":{"field":"severity","type":"nominal","sort":sev,"title":None,"axis":{"labelLimit":230}}},
  "layer":[{"mark":{"type":"bar","tooltip":True},"encoding":{"x":{"field":"pct","type":"quantitative","title":"%"},"yOffset":{"field":"sex"},
   "color":{"field":"sex","type":"nominal","scale":{"domain":["Males","Females"],"range":["#2a6f97","#e07a5f"]},"legend":{"title":None,"orient":"top"}},
   "tooltip":[{"field":"severity"},{"field":"sex"},{"field":"pct"},{"field":"lo"},{"field":"hi"}]}},
  {"mark":{"type":"rule","color":"#333"},"encoding":{"x":{"field":"lo","type":"quantitative"},"x2":{"field":"hi"},"yOffset":{"field":"sex"}}}]}})

# 7 hospitalisations: share of separations with obesity code
for d in co: d['pct_with_obesity']=round(100*d['with_obesity']/d['total_separations'],2)
save('7_hospitalisations.vl.json',{"$schema":S,"config":cfg,"title":"Share of each diagnosis's hospital separations that carry an obesity (U78.1) code","data":{"values":co},
 "vconcat":[{"width":480,"height":{"step":20},"mark":{"type":"bar","color":"#1d7874","tooltip":True},
  "encoding":{"y":{"field":"diagnosis","type":"nominal","sort":"-x","title":None,"axis":{"labelLimit":340}},"x":{"field":"pct_with_obesity","type":"quantitative","title":"% of diagnosis separations with obesity coded"},
  "tooltip":[{"field":"diagnosis"},{"field":"with_obesity","format":","},{"field":"total_separations","format":","},{"field":"pct_with_obesity","title":"%"}]}}]})

# 8 cost
r=rd('Price-Gender-Age.csv'); ct=[]; ages=[]
for row in r[4:]:
    a=row[0].strip()
    if a=='All ages' or not a: continue
    ages.append(a)
    for s,i in(('Males',2),('Females',5)):
        ct+= [{"age":a,"sex":s,"type":"Treatment & management of obesity","aud_m":num(row[i])/1e6},{"age":a,"sex":s,"type":"Treatment of conditions due to overweight","aud_m":num(row[i+1])/1e6}]
save('8_cost.vl.json',{"$schema":S,"config":cfg,"title":"Health expenditure on overweight and obesity by age and sex, 2023–24 ($m)","data":{"values":ct},
 "facet":{"row":{"field":"sex","type":"nominal","title":None,"sort":["Males","Females"]}},
 "spec":{"width":560,"height":200,"mark":{"type":"bar","tooltip":True},"encoding":{"x":{"field":"age","type":"ordinal","sort":ages,"title":"Age group","axis":{"labelAngle":-40}},
  "y":{"field":"aud_m","type":"quantitative","title":"$ million"},"color":{"field":"type","type":"nominal","scale":{"range":["#e9c46a","#264653"]},"legend":{"title":None,"orient":"top","labelLimit":320,"columns":1}},
  "tooltip":[{"field":"age"},{"field":"type"},{"field":"aud_m","format":",.1f","title":"$m"}]}}})

# 9 GLP1 template
save('9_glp1_and_other_treatment.vl.json',{"$schema":S,"config":cfg,"description":"TEMPLATE – no GLP-1 / treatment data was in the uploaded files. Replace data.url with a CSV with columns: year, treatment, value (e.g. PBS scripts or patients).",
 "title":"GLP-1 and other obesity treatments over time","data":{"url":"GLP1-Treatment.csv"},
 "mark":{"type":"line","point":True,"tooltip":True},"width":520,"height":320,
 "encoding":{"x":{"field":"year","type":"ordinal","title":None},"y":{"field":"value","type":"quantitative","title":"Prescriptions / patients"},"color":{"field":"treatment","type":"nominal","title":None}}})

open(O+'GLP1-Treatment.csv','w').write('year,treatment,value\n')

# extra tidy dataset: children (not charted)
r=rd('Children-Age-Rate-Gender.csv'); ch=[]
for row in r[5:]:
    if not row[0]: continue
    for grp,b0 in (('Boys',1),('Girls',10),('All children',19)):
        for k,m in enumerate(('Overweight but not obese','Obese','Overweight or obese')):
            i=b0+3*k; lo,hi=ci(row[i+1]); ch.append({"age_group":row[0],"group":grp,"measure":m,"pct":num(row[i]),"lo":lo,"hi":hi})
w=csv.DictWriter(open(O+'children_overweight_obesity.csv','w',newline='',encoding='utf-8'),fieldnames=ch[0].keys()); w.writeheader(); w.writerows(ch)
import shutil; shutil.copy('/home/claude/build.py',O+'build_datasets_and_specs.py')
