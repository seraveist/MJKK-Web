from src.lang import zh, kanji, ja, katakana, romaji, en, kr
import math

s=kr

def generate_hand(baihais, tsumohais, sutehais):
    baihaisTemp = []
    for temp in baihais:
      baihaisTemp.append(temp)

    tsumohaisTemp = []
    for temp in tsumohais:
      tsumohaisTemp.append(temp)

    sutehaisTemp = []
    for temp in sutehais:
      sutehaisTemp.append(temp)

    for i, sutehai in enumerate(sutehaisTemp):
        baihaisTemp.append(tsumohaisTemp[i])
        if type(sutehai) == str:
          if "r" in sutehai:
              richiPai = int(sutehaisTemp[i].lstrip("r"))
              if richiPai == 60:
                  baihaisTemp.remove(tsumohaisTemp[i])
              else:
                  baihaisTemp.remove(richiPai)
              break
        else:
            if sutehai == 60:
                baihaisTemp.remove(tsumohaisTemp[i])
            else:
                baihaisTemp.remove(sutehaisTemp[i])
    
    convertBaihai = []
    for tile in baihaisTemp:
        if tile > 50:
            convertBaihai.append((tile-51) * 10 + 5)
        else:
            convertBaihai.append(tile - 10)
			
    return convertBaihai


def output_hai(tehai1:int,is_number_only:bool=False,jihai_in_kanji:bool=True)->str:
	if not is_number_only:
		if tehai1<30 or not jihai_in_kanji:
			return str(tehai1%10)+('m','p','s','z')[tehai1//10]
		elif jihai_in_kanji:
			return ('東','南','西','北','白','發','中')[tehai1-31]
	else:
		return str(tehai1)

def output_hais(tehai1:list,is_number_only:bool=False,jihai_in_kanji:bool=True,end:str="")->str:
	string=""
	if not is_number_only:
		string_manzu=''.join(str(i) for i in tehai1 if i and i<10)+("m" if any(i in tehai1 for i in range(1,10)) else "")
		string_pinzu=''.join(str(i-10) for i in tehai1 if i and 10<i<20)+("p" if any(i in tehai1 for i in range(11,20)) else "")
		string_soozu=''.join(str(i-20) for i in tehai1 if i and 20<i<30)+("s" if any(i in tehai1 for i in range(21,30)) else "")
		if jihai_in_kanji:
			string_jihai=' '.join(('東','南','西','北','白','發','中')[i-31]*(tehai1.count(i)) for i in range(30,38) if tehai1.count(i))
		else:
			string_jihai=''.join(str(i-30) for i in tehai1 if i and 30<i<38)+("z" if any(i in tehai1 for i in range(30,38)) else "")
		string=' '.join(i for i in (string_manzu,string_pinzu,string_soozu,string_jihai) if i)
	else:
		for i in tehai1:
			if i==None:
				pass
			else:
				string+=str(i)
	return string+end

def yaku_and_output(tehai9:list,hoorakei:list,did_tsumo:bool,is_karaten:bool,tsumohai:int,dahai:int,is_number_only:bool=False,has_koyaku:bool=False)->('hansuu',str):
	yaku=[]
	hansuu=0
	is_yakuman=False

	#kokushimusou
	if len(hoorakei)>1 and hoorakei[1][0]=='tp':
		if tehai9[tsumohai]==2:
			yaku.append(s.kokushimusoujuusanmen)
			hansuu+=26
		else:
			yaku.append(s.kokushimusou)
			hansuu+=13
		is_yakuman=True

	elif sum(tehai9)<=14:

		#tanyaochuu
		if sum(tehai9)==14 and not tehai9[1] and not tehai9[9] and not tehai9[11] and not tehai9[19] and not tehai9[21] and not tehai9[29] and not any(tehai9[31:]):
			yaku.append(s.tanyaochuu)
			hansuu+=1

		#yakuhai
		#not checking chanfon or menfon
		#ton
		if ['k',31,31,31] in hoorakei:
			yaku.append(s.yakuhai_ton+s.question_mark)
			hansuu+=1
		#nan
		if ['k',32,32,32] in hoorakei:
			yaku.append(s.yakuhai_nan+s.question_mark)
			hansuu+=1
		#shaa
		if ['k',33,33,33] in hoorakei:
			yaku.append(s.yakuhai_shaa+s.question_mark)
			hansuu+=1
		#pei
		if ['k',34,34,34] in hoorakei:
			yaku.append(s.yakuhai_pei+s.question_mark)
			hansuu+=1
		if sum((i in yaku for i in (s.yakuhai_ton+s.question_mark,s.yakuhai_nan+s.question_mark,s.yakuhai_shaa+s.question_mark,s.yakuhai_pei+s.question_mark)))==3:
			hansuu-=1
		#haku
		if ['k',35,35,35] in hoorakei:
			yaku.append(s.yakuhai_haku)
			hansuu+=1
		#hatsu
		if ['k',36,36,36] in hoorakei:
			yaku.append(s.yakuhai_hatsu)
			hansuu+=1
		#chun
		if ['k',37,37,37] in hoorakei:
			yaku.append(s.yakuhai_chun)
			hansuu+=1

		#pinfu
		#not checking chanfon or menfon
		if len(hoorakei)==5 and all(i[0]=='s' for i in hoorakei[1:]) and hoorakei[0][1]<35:
			if did_tsumo==False and tsumohai<30:
				if any((tsumohai==i[1] and tsumohai not in (7,17,27)) or (tsumohai==i[3] and tsumohai not in (3,13,23)) for i in hoorakei[1:]):
					if hoorakei[0][1]>30:
						yaku.append(s.pinfu+s.question_mark)
					else:
						yaku.append(s.pinfu)
					hansuu+=1
			else:
				yaku.append(s.pinfu+s.question_mark)
				hansuu+=1

		#iipeekoo
		#not checking menzenchin
		if any(i[0]=='s' and hoorakei.count(i)>=2 for i in hoorakei):
			yaku.append(s.iipeekoo)
			hansuu+=1

		#chiitoitsu
		if hoorakei[0][0]=='t':
			yaku.append(s.chiitoitsu)
			hansuu+=2

		#sanshokudoujun
		if any(all(['s',i+j,i+1+j,i+2+j] in hoorakei for j in (0,10,20)) for i in range(1,8)):
			yaku.append(s.sanshokudoujun)
			hansuu+=2#not counting kuisagari

		#ikkitsuukan
		if any(all(['s',1+j+i,2+j+i,3+j+i] in hoorakei for j in (0,3,6)) for i in (0,10,20)):
			yaku.append(s.ikkitsuukan)
			hansuu+=2#not counting kuisagari

		#honchantaiyaochuu
		if len(hoorakei)==5 and all(i[1] in (1,11,21,9,19,29) or i[3] in (9,19,29) or i[1]>30 for i in hoorakei) and any(i[0]=='s' for i in hoorakei) and 0<sum(tehai9[31:])<14:
			yaku.append(s.honchantaiyaochuu)
			hansuu+=2#not counting kuisagari

		#toitoihoo
		if len(hoorakei)==5 and all(i[0]=='k' for i in hoorakei[1:]):
			yaku.append(s.toitoihoo)
			hansuu+=2

		#sanankoo
		#not checking fuuro
		if sum(i[0]=='k' for i in hoorakei)>=3:
			if did_tsumo==False and any(i[0]!='k' and tsumohai in i for i in hoorakei) or s.toitoihoo in yaku:
				yaku.append(s.sanankoo)
			else:
				yaku.append(s.sanankoo+s.question_mark)
			hansuu+=2

		#honroutou
		if tehai9[1]+tehai9[9]+tehai9[11]+tehai9[19]+tehai9[21]+tehai9[29]+sum(tehai9[31:])==14 and 0<sum(tehai9[31:])<14:
			yaku.append(s.honroutou)
			hansuu+=2

		#sanshokudookoo
		if any((['k',i,i,i] in hoorakei and ['k',i+10,i+10,i+10] in hoorakei and ['k',i+20,i+20,i+20] in hoorakei) for i in range(1,10)):
				yaku.append(s.sanshokudookoo)
				hansuu+=2

		#shousangen
		if (['j',35,35,None]==hoorakei[0] and ['k',36,36,36] in hoorakei and ['k',37,37,37] in hoorakei) or \
		(['k',35,35,35] in hoorakei and ['j',36,36,None]==hoorakei[0] and ['k',37,37,37] in hoorakei) or \
		(['k',35,35,35] in hoorakei and ['k',36,36,36] in hoorakei and ['j',37,37,None]==hoorakei[0]):
			yaku.append(s.shousangen)
			hansuu+=2

		if has_koyaku:
			#uumensai
			if all((any(tehai9[1:10]),any(tehai9[11:20]),any(tehai9[21:30]),any(tehai9[31:35]),any(tehai9[35:58]))):
				yaku.append(s.uumensai)
				hansuu+=2

			#sanrenkoo
			if any(i%10<=7 and ['k',i+1,i+1,i+1] in hoorakei and ['k',i+2,i+2,i+2] in hoorakei for [h,i,j,k] in hoorakei if h=='k' and i<=27):
				yaku.append(s.sanrenkoo)
				hansuu+=2

		#honiisoo
		if sum(tehai9)==14 and 0<sum(tehai9[31:])<14 and (not any(tehai9[11:30]) or not any(tehai9[1:10]+tehai9[21:30]) or not any(tehai9[1:20])):
			yaku.append(s.honiisoo)
			hansuu+=3#not counting kuisagari

		#junchantaiyaochuu
		if len(hoorakei)==5 and all(i[1] in (1,11,21,9,19,29) or i[3] in (9,19,29) for i in hoorakei) and any(i[0]=='s' for i in hoorakei):
			yaku.append(s.junchantaiyaochuu)
			hansuu+=3#not counting kuisagari

		#ryanpeekoo
		#not checking menzenchin
		if sum(i[0]=='s' and hoorakei.count(i)>=2 for i in hoorakei)>=4:
			yaku.append(s.ryanpeekoo)
			yaku.remove(s.iipeekoo)
			hansuu+=2

		if has_koyaku:
			#isshokusanjun
			if any(i%10<=7 and hoorakei.count(['s',i,i+1,i+2])>=3 for [h,i,j,k] in hoorakei if h=='s' and i<=27):
				yaku.append(s.isshokusanjun)
				hansuu+=3#not counting kuisagari

		#chiniisoo
		if sum(tehai9)==14 and (sum(tehai9[1:10])==14 or sum(tehai9[11:20])==14 or sum(tehai9[21:30])==14):
			yaku.append(s.chiniisoo)
			hansuu+=6#not counting kuisagari

		#suuankoo
		#not checking menzenchin
		if sum(i[0]=='k' for i in hoorakei)>=4:
			if did_tsumo==False:
				if tsumohai==hoorakei[0][1]:
					yaku.append(s.suuankootanki)
					hansuu+=26
					is_yakuman=True
				else:
					yaku.append(s.sanankoo+s.ideographic_comma+s.toitoihoo+' ('+s.suuankoo+s.question_mark+')')
					hansuu+=4
					is_yakuman=False
			else:
				yaku.append(s.suuankoo+s.question_mark)
				hansuu+=13
				is_yakuman=True
			yaku.remove(s.toitoihoo)
			hansuu-=2
			if s.sanankoo+s.question_mark in yaku:
				yaku.remove(s.sanankoo+s.question_mark)
				hansuu-=2
			if s.sanankoo in yaku:
				yaku.remove(s.sanankoo)
				hansuu-=2

		#daisangen
		if ['k',35,35,35] in hoorakei and ['k',36,36,36] in hoorakei and ['k',37,37,37] in hoorakei:
			yaku.append(s.daisangen)
			is_yakuman=True
			yaku.remove(s.yakuhai_haku)
			yaku.remove(s.yakuhai_hatsu)
			yaku.remove(s.yakuhai_chun)
			hansuu+=10

		#tsuuiisoo
		if sum(tehai9)==14==sum(tehai9[31:]):
			yaku.append(s.tsuuiisoo)
			hansuu+=13
			is_yakuman=True

		#shousuushii
		if any(hoorakei[0]==['j',i,i,None] for i in range(31,35)) and all(hoorakei[0]==['j',i,i,None] or ['k',i,i,i] in hoorakei for i in range(31,35)):
			yaku.append(s.shousuushii)
			hansuu+=13
			is_yakuman=True

		#ryuuiisoo
		if sum(tehai9)==14==tehai9[22]+tehai9[23]+tehai9[24]+tehai9[26]+tehai9[28]+tehai9[36]:
			yaku.append(s.ryuuiisoo)
			hansuu+=13
			is_yakuman=True

		#chinroutou
		if sum(tehai9)==14==tehai9[1]+tehai9[9]+tehai9[11]+tehai9[19]+tehai9[21]+tehai9[29]:
			yaku.append(s.chinroutou)
			hansuu+=13
			is_yakuman=True
			if s.toitoihoo in yaku:
				yaku.remove(s.toitoihoo)
				hansuu-=2

		#chuurenpouton
		#not checking menzenchin
		if sum(tehai9)==14 and any(tehai9[i+1]>=3 and all(tehai9[i+2:i+9]) and tehai9[i+9]>=3 for i in (0,10,20)):
			if did_tsumo==False:
				if tsumohai%10 in (1,9) and tehai9[tsumohai]==4 or tehai9[tsumohai]==2:
					yaku.append(s.junseichuurenpouton)
					hansuu+=26
					is_yakuman=True
				else:
					yaku.append(s.chuurenpouton)
					hansuu+=13
					is_yakuman=True
			else:
				yaku.append(s.chuurenpouton)
				hansuu+=13
				is_yakuman=True
			yaku.remove(s.chiniisoo)
			hansuu-=6#not checking kuisagari

		#daisuushii
		if ['k',31,31,31] in hoorakei and ['k',32,32,32] in hoorakei and ['k',33,33,33] in hoorakei and ['k',34,34,34] in hoorakei:
			yaku.append(s.daisuushii)
			is_yakuman=True
			yaku.remove(s.yakuhai_ton+s.question_mark)
			yaku.remove(s.yakuhai_nan+s.question_mark)
			yaku.remove(s.yakuhai_shaa+s.question_mark)
			yaku.remove(s.yakuhai_pei+s.question_mark)
			hansuu+=22
			if s.toitoihoo in yaku:
				yaku.remove(s.toitoihoo)
				hansuu-=2

		if has_koyaku:
			if is_number_only:
				#daisuurin
				if s.chiitoitsu in yaku and all(i==2 for i in tehai9[2:9]):
					yaku.append(s.daisharin)
					is_yakuman=True
					yaku.remove(s.tanyaochuu)
					yaku.remove(s.chiitoitsu)
					yaku.remove(s.chiniisoo)
					hansuu+=4
			else:
				#daisuurin
				if s.chiitoitsu in yaku and all(i==2 for i in tehai9[2:9]):
					yaku.append(s.daisuurin)
					is_yakuman=True
					yaku.remove(s.tanyaochuu)
					yaku.remove(s.chiitoitsu)
					yaku.remove(s.chiniisoo)
					hansuu+=4
				#daisharin
				if s.chiitoitsu in yaku and all(i==2 for i in tehai9[12:19]):
					yaku.append(s.daisharin)
					is_yakuman=True
					yaku.remove(s.tanyaochuu)
					yaku.remove(s.chiitoitsu)
					yaku.remove(s.chiniisoo)
					hansuu+=4
				#daichikurin
				if s.chiitoitsu in yaku and all(i==2 for i in tehai9[22:29]):
					yaku.append(s.daichikurin)
					is_yakuman=True
					yaku.remove(s.tanyaochuu)
					yaku.remove(s.chiitoitsu)
					yaku.remove(s.chiniisoo)
					hansuu+=4

			#daichisei
			if s.chiitoitsu in yaku and all(i==2 for i in tehai9[31:38]):
				yaku.append(s.daichisei)
				is_yakuman=True
				yaku.remove(s.chiitoitsu)
				yaku.remove(s.tsuuiisoo)
				hansuu+=11

	#output
	string=""
	if dahai:
		string+=s.da+" ["+output_hai(dahai,is_number_only)+"] "
	if did_tsumo:
		string+=s.hoora+" | "
	elif did_tsumo==False:
		string+=(s.karaten if is_karaten else s.tenpai)+" ["+output_hai(tsumohai,is_number_only)+"] | "
	for j in hoorakei:
		string+=output_hais(j[1:],is_number_only,True," ")
	string+="|"
	if is_yakuman and hansuu>=13:
		string+=" "+s.yakuman_level_list[hansuu//13]+s.colon
	elif not is_yakuman and hansuu>=13:
		string+=" "+s.kazoeyakuman+"("+str(hansuu)+s.han+")"+s.colon
	elif hansuu>0:
		string+=str(hansuu).rjust(3)+s.han+s.colon
	string+=s.ideographic_comma.join(yaku)+" "

	return hansuu,string

def GotHoorahai(tehai1:list=None,dahai:int=None,is_number_only:bool=False,has_koyaku:bool=False)->str:
	string=[]
	string_chiniisoo_chart=[]

	tehai1.sort()

	#count tehai
	haisuu=len(tehai1)
	tehai9=[0]*38
	for i in tehai1:
		tehai9[i]+=1

	is_chiniisoo=False
	if 13<=sum(tehai9) and (sum(tehai9)==sum(tehai9[1:10]) or sum(tehai9)==sum(tehai9[11:20]) or sum(tehai9)==sum(tehai9[21:30])):
		is_chiniisoo=True

	if haisuu==0:
		return string

	mentsusuu=haisuu//3
	is_tenpai=False
	is_beginning_of_the_cosmos=False
	kouten=[]

	if haisuu==tehai9[35]==18:
		is_beginning_of_the_cosmos=True
		did_tsumo=True
	elif haisuu%3==2:
		did_tsumo=True
	elif haisuu%3==1:
		did_tsumo=False
		haisuu+=1
		agarihais=[]
	elif haisuu%3==0:
		did_tsumo=None
		string.append(s.taapai_or_shaopai.format(str(haisuu)))
		return string

	for tsumohai in range(1,10 if is_number_only else 38):
		if tsumohai%10==0:
			continue

		is_karaten=False
		if did_tsumo==False:
			tehai9[tsumohai]+=1
			if tehai9[tsumohai]==5:
				is_karaten=True

		is_hoora=False
		hoorakeis=[]
		hansuu=[]

		#kokushimusou
		if haisuu==14 and not any(tehai9[2:9]) and not any(tehai9[12:19]) and not any(tehai9[22:29]) and tehai9[1] and tehai9[9] and tehai9[11] and tehai9[19] and tehai9[21] and tehai9[29] and all(tehai9[31:]):
			is_hoora=True
			hoorakeis.append([['j',tehai9.index(2),tehai9.index(2),None]]+[['tp',i,None,None] for i in range(38) if tehai9[i]==1])
			hansuu_temp,string_temp=yaku_and_output(tehai9,hoorakeis[-1],did_tsumo,is_karaten,tsumohai,dahai,is_number_only,has_koyaku)
			hansuu.append(hansuu_temp)
			string.append(string_temp)
		else:

			#chiitoitsu
			if haisuu==14 and tehai9.count(2)==7:
				is_hoora=True
				hoorakeis.append([['t',i,i,None] for i in range(10 if is_number_only else 38) if tehai9[i]==2])
				hansuu_temp,string_temp=yaku_and_output(tehai9,hoorakeis[-1],did_tsumo,is_karaten,tsumohai,dahai,is_number_only,has_koyaku)
				hansuu.append(hansuu_temp)
				string.append(string_temp)

			#analyse tehai
			#jantou
			for jantou_i in range(10 if is_number_only else 38):
				if tehai9[jantou_i]>=2:
					hoorakei_temp=[['j',jantou_i,jantou_i,None]]
					tehai9_temp=tehai9.copy()
					tehai9_temp[jantou_i]-=2
				else:
					continue

				#mentsu
				for mentsu_i in range(mentsusuu+1):
					if tehai9_temp==None:
						break
					elif sum(tehai9_temp)==0:
						is_hoora=True
						hoorakei_temp.sort()
						if hoorakei_temp not in hoorakeis:
							hoorakeis.append(hoorakei_temp)
							hansuu_temp,string_temp=yaku_and_output(tehai9,hoorakei_temp,did_tsumo,is_karaten,tsumohai,dahai,is_number_only,has_koyaku)
							hansuu.append(hansuu_temp)
							string.append(string_temp)
							#if sanrenkoo then change to 3-shuntsu
							hoorakei_new_num=1
							while hoorakei_new_num:
								hoorakei_new_num_temp=hoorakei_new_num
								hoorakei_new_num=0
								for hoorakei_i in hoorakeis[-hoorakei_new_num_temp:]:
									for mentsu_picked_i in hoorakei_i[1:]:
										if mentsu_picked_i[0]=='k':
											kootsu_hai=mentsu_picked_i[1]
											if kootsu_hai%10<=7 and kootsu_hai<30 and ['k',kootsu_hai+1,kootsu_hai+1,kootsu_hai+1] in hoorakei_i and ['k',kootsu_hai+2,kootsu_hai+2,kootsu_hai+2] in hoorakei_i:
												hoorakei_temp=hoorakei_i.copy()
												hoorakei_temp.remove(mentsu_picked_i)
												hoorakei_temp.remove(['k',kootsu_hai+1,kootsu_hai+1,kootsu_hai+1])
												hoorakei_temp.remove(['k',kootsu_hai+2,kootsu_hai+2,kootsu_hai+2])
												hoorakei_temp.extend([['s',kootsu_hai,kootsu_hai+1,kootsu_hai+2]]*3)
												hoorakei_temp.sort()
												if hoorakei_temp not in hoorakeis:
													hoorakeis.append(hoorakei_temp)
													hoorakei_new_num+=1
													hansuu_temp,string_temp=yaku_and_output(tehai9,hoorakei_temp,did_tsumo,is_karaten,tsumohai,dahai,is_number_only,has_koyaku)
													hansuu.append(hansuu_temp)
													string.append(string_temp)
						continue
					for hai_picked in range(10 if is_number_only else 38):
						if tehai9_temp[hai_picked]==0:
							continue
						elif tehai9_temp[hai_picked]>=3:#kootsu exists
							tehai9_temp[hai_picked]-=3
							hoorakei_temp.append(['k',hai_picked,hai_picked,hai_picked])
							break
						elif hai_picked<28 and all(tehai9_temp[hai_picked:hai_picked+3]):#shuntsu exists
							tehai9_temp[hai_picked]-=1
							tehai9_temp[hai_picked+1]-=1
							tehai9_temp[hai_picked+2]-=1
							hoorakei_temp.append(['s',hai_picked,hai_picked+1,hai_picked+2])
							break
						else:#neither kootsu nor shuntsu exists
							tehai9_temp=None
							break

		if did_tsumo==False and is_hoora:
			is_tenpai=True
			if not is_karaten:
				agarihais.append(tsumohai)
				if max(hansuu)>=13:
					kouten.append(max(hansuu)//13*13)
					if dahai and is_chiniisoo and tehai1[0]//10==tsumohai//10:
						string_chiniisoo_chart.append((str(max(hansuu)//13*13))[:5].ljust(3).rjust(5))
				else:
					kouten.append(max(hansuu))
					if dahai and is_chiniisoo and tehai1[0]//10==tsumohai//10:
						string_chiniisoo_chart+=(str(max(hansuu)))[:5].ljust(3).rjust(5)+"|"
		if did_tsumo==False and dahai and (not is_hoora or is_karaten) and is_chiniisoo and tehai1[0]//10==tsumohai//10:
			string_chiniisoo_chart+="     |"

		if did_tsumo and not is_hoora:
			if is_beginning_of_the_cosmos:
				string.append(s.hoora+" | 55z 5555z 5555z 5555z 5555z | "+s.beginning_of_the_cosmos+"(140"+s.fuu+"105"+s.han+" 90865195024359483499283685761351700"+s.ten+")"+s.colon+s.tsuuiisoo+s.ideographic_comma+s.sanankoo+s.ideographic_comma+s.suukantsu+s.ideographic_comma+s.rinshankaihou+s.ideographic_comma+s.yakuhai_haku+"4"+s.ideographic_comma+s.dora+"72")
			else:
				string.append(s.not_hoora)
				#dahai
				if is_chiniisoo:
					string_chiniisoo_chart.append(" 打\\和 1 |  2  |  3  |  4  |  5  |  6  |  7  |  8  |  9  | ")
				for sutehai_i in range(10 if is_number_only else 38):
					if sutehai_i in tehai1:
						tehai1_new=tehai1.copy()
						tehai1_new.remove(sutehai_i)
						if is_chiniisoo:
							string_chiniisoo_chart.append(str(sutehai_i%10))
						a,b=GotHoorahai(tehai1=tehai1_new,dahai=sutehai_i,is_number_only=is_number_only,has_koyaku=has_koyaku)
						string.append(a)
						string_chiniisoo_chart.append(b)

		if did_tsumo:
			break
		if did_tsumo==False:
			tehai9[tsumohai]-=1

	#tenpai
	if not dahai and is_tenpai and agarihais:
		string.append(s.tenpai+s.colon)
		agarihai_list = []
		if not is_number_only:
			agarihai_han=list(zip(agarihais,kouten))
			agarihai_han.sort(key=lambda elem: (elem[1],elem[0]))

			agarihai_list = []
			agaricase = []
			for agarihai_han_i in range(len(agarihai_han)):
				agaricase.append(output_hai(agarihai_han[agarihai_han_i][0],is_number_only))
				if(agarihai_han_i!=len(agarihai_han)-1 and agarihai_han[agarihai_han_i][1]!=agarihai_han[agarihai_han_i+1][1]) or agarihai_han_i==len(agarihai_han)-1 and haisuu<=14:
					if agarihai_han[agarihai_han_i][1]>=13:
						agaricase.append("("+s.yakuman_level_list[agarihai_han[agarihai_han_i][1]//13]+")")
					else:
						agaricase.append("("+str(agarihai_han[agarihai_han_i][1])+s.han+")")
				
				agarihai_list.append(agaricase)
				agaricase = []
		else:
			for agarihai_i in agarihais:
				agarihai_list.append(output_hai(agarihai_i,is_number_only))
		
		string.append(agarihai_list)

	#nooten
	if did_tsumo==False and not dahai and not is_tenpai:
		string.append(s.nooten)

	return string,string_chiniisoo_chart

def InputShonhai(tehai:str=None,tehai1:list=None,dahai:int=None,is_number_only:bool=False,has_koyaku:bool=False)->str:
	string = []
	result = []

	#input tehai
	if tehai1==None:
		tehai_lower=tehai.lower()
		for i in (' ','!','"','#','$','%','&','\'','(',')','*','+',',','-','.','/',':',';','<','=','>','?','@','[','\\',']','^','_','`','{','|','}','~','　','\n','\r','\t'):
			tehai=tehai.replace(i,'')
		if tehai=='':
			return ''

		#manage tehai
		tehai1=[]
		shurui_now=None
		shurui_used=True
		invalid_inputs=[]
		has_0=False
		has_0m=False
		has_0p=False
		has_0s=False
		#number only
		if tehai.isdecimal():
			is_number_only=True
			if '0' in tehai:
				has_0=True
			tehai1=[int(i) if i!='0' else 5 for i in tehai]
		else:
			tehai=tehai[::-1]
			for tehai_i in tehai:
				if tehai_i in ('E','Ｅ','東','东'):
					tehai1.append(31)
				elif tehai_i in ('S','Ｓ','南'):
					tehai1.append(32)
				elif tehai_i in ('W','Ｗ','西'):
					tehai1.append(33)
				elif tehai_i in ('N','Ｎ','北'):
					tehai1.append(34)
				elif tehai_i in ('P','D','Ｐ','Ｄ','白'):
					tehai1.append(35)
				elif tehai_i in ('F','H','R','Ｆ','Ｈ','Ｒ','發','発','发'):
					tehai1.append(36)
				elif tehai_i in ('C','Ｃ','中'):
					tehai1.append(37)
				elif tehai_i in ('m','w','ｍ','ｗ','万','萬'):
					if not shurui_used:
						invalid_inputs.insert(0,('m','p','s','z')[shurui_now])
					shurui_now=0
					shurui_used=False
				elif tehai_i in ('p','ｐ','筒','饼','餠','餅'):
					if not shurui_used:
						invalid_inputs.insert(0,('m','p','s','z')[shurui_now])
					shurui_now=1
					shurui_used=False
				elif tehai_i in ('s','ｓ','索','条','條'):
					if not shurui_used:
						invalid_inputs.insert(0,('m','p','s','z')[shurui_now])
					shurui_now=2
					shurui_used=False
				elif tehai_i in ('z','ｚ','字'):
					if not shurui_used:
						invalid_inputs.insert(0,('m','p','s','z')[shurui_now])
					shurui_now=3
					shurui_used=False
				elif tehai_i.isdecimal():
					if shurui_now!=None:
						if tehai_i=='0' and shurui_now in (0,1,2):
							tehai1.append(5+shurui_now*10)
							if shurui_now==0:
								has_0m=True
							elif shurui_now==1:
								has_0p=True
							elif shurui_now==2:
								has_0s=True
						elif tehai_i in ('0','8','9') and shurui_now==3:
							invalid_inputs.insert(0,tehai_i+'z')
							shurui_used=True
						else:
							tehai1.append(int(tehai_i)+shurui_now*10)
						shurui_used=True
					else:
						invalid_inputs.insert(0,tehai_i)
				else:
					if not shurui_used:
						invalid_inputs.insert(0,('m','p','s','z')[shurui_now])
						shurui_used=True
					invalid_inputs.insert(0,tehai_i)
			if shurui_used==False:
				invalid_inputs.insert(0,('m','p','s','z')[shurui_now])

		if invalid_inputs:
			result.append(s.ideographic_comma.join(invalid_inputs))

		if has_0:
			string.append(s.has_0)
		elif has_0m:
			string.append(s.has_0m)
		elif has_0p:
			string.append(s.has_0p)
		elif has_0s:
			string+=(s.has_0s)

	tehai1.sort()

	#count tehai
	haisuu=len(tehai1)
	tehai9=[0]*38
	for i in tehai1:
		tehai9[i]+=1

	is_chiniisoo=False
	if 13<=sum(tehai9) and (sum(tehai9)==sum(tehai9[1:10]) or sum(tehai9)==sum(tehai9[11:20]) or sum(tehai9)==sum(tehai9[21:30])):
		is_chiniisoo=True

	if haisuu==0:
		result.append(string)
		return result

	#show tehai
	if not dahai:
		string.append(s.tehai+s.colon+output_hais(tehai1,is_number_only,jihai_in_kanji=True,end=""))

		if any(i>4 for i in tehai9):
			string.append(s.more_than_4.format(s.ideographic_comma.join([output_hai(i,is_number_only) for i in range(10 if is_number_only else 38) if tehai9[i]>4])))

		if haisuu>14:
			string.append(s.more_than_14.format(str(haisuu)))
		if haisuu<13:
			string.append(s.less_than_13.format(str(haisuu)))

	mentsusuu=haisuu//3
	is_tenpai=False
	is_beginning_of_the_cosmos=False
	kouten=[]

	if haisuu==tehai9[35]==18:
		is_beginning_of_the_cosmos=True
		did_tsumo=True
	elif haisuu%3==2:
		did_tsumo=True
	elif haisuu%3==1:
		did_tsumo=False
		haisuu+=1
		agarihais=[]
	elif haisuu%3==0:
		did_tsumo=None
		string.append(s.taapai_or_shaopai.format(str(haisuu)))
		result.append(string)
		return result

	for tsumohai in range(1,10 if is_number_only else 38):
		if tsumohai%10==0:
			continue

		is_karaten=False
		if did_tsumo==False:
			tehai9[tsumohai]+=1
			if tehai9[tsumohai]==5:
				is_karaten=True

		is_hoora=False
		hoorakeis=[]
		hansuu=[]

		#kokushimusou
		if haisuu==14 and not any(tehai9[2:9]) and not any(tehai9[12:19]) and not any(tehai9[22:29]) and tehai9[1] and tehai9[9] and tehai9[11] and tehai9[19] and tehai9[21] and tehai9[29] and all(tehai9[31:]):
			is_hoora=True
			hoorakeis.append([['j',tehai9.index(2),tehai9.index(2),None]]+[['tp',i,None,None] for i in range(38) if tehai9[i]==1])
			hansuu_temp,string_temp=yaku_and_output(tehai9,hoorakeis[-1],did_tsumo,is_karaten,tsumohai,dahai,is_number_only,has_koyaku)
			hansuu.append(hansuu_temp)
			string.append(string_temp)
		else:

			#chiitoitsu
			if haisuu==14 and tehai9.count(2)==7:
				is_hoora=True
				hoorakeis.append([['t',i,i,None] for i in range(10 if is_number_only else 38) if tehai9[i]==2])
				hansuu_temp,string_temp=yaku_and_output(tehai9,hoorakeis[-1],did_tsumo,is_karaten,tsumohai,dahai,is_number_only,has_koyaku)
				hansuu.append(hansuu_temp)
				string.append(string_temp)

			#analyse tehai
			#jantou
			for jantou_i in range(10 if is_number_only else 38):
				if tehai9[jantou_i]>=2:
					hoorakei_temp=[['j',jantou_i,jantou_i,None]]
					tehai9_temp=tehai9.copy()
					tehai9_temp[jantou_i]-=2
				else:
					continue

				#mentsu
				for mentsu_i in range(mentsusuu+1):
					if tehai9_temp==None:
						break
					elif sum(tehai9_temp)==0:
						is_hoora=True
						hoorakei_temp.sort()
						if hoorakei_temp not in hoorakeis:
							hoorakeis.append(hoorakei_temp)
							hansuu_temp,string_temp=yaku_and_output(tehai9,hoorakei_temp,did_tsumo,is_karaten,tsumohai,dahai,is_number_only,has_koyaku)
							hansuu.append(hansuu_temp)
							string.append(string_temp)
							#if sanrenkoo then change to 3-shuntsu
							hoorakei_new_num=1
							while hoorakei_new_num:
								hoorakei_new_num_temp=hoorakei_new_num
								hoorakei_new_num=0
								for hoorakei_i in hoorakeis[-hoorakei_new_num_temp:]:
									for mentsu_picked_i in hoorakei_i[1:]:
										if mentsu_picked_i[0]=='k':
											kootsu_hai=mentsu_picked_i[1]
											if kootsu_hai%10<=7 and kootsu_hai<30 and ['k',kootsu_hai+1,kootsu_hai+1,kootsu_hai+1] in hoorakei_i and ['k',kootsu_hai+2,kootsu_hai+2,kootsu_hai+2] in hoorakei_i:
												hoorakei_temp=hoorakei_i.copy()
												hoorakei_temp.remove(mentsu_picked_i)
												hoorakei_temp.remove(['k',kootsu_hai+1,kootsu_hai+1,kootsu_hai+1])
												hoorakei_temp.remove(['k',kootsu_hai+2,kootsu_hai+2,kootsu_hai+2])
												hoorakei_temp.extend([['s',kootsu_hai,kootsu_hai+1,kootsu_hai+2]]*3)
												hoorakei_temp.sort()
												if hoorakei_temp not in hoorakeis:
													hoorakeis.append(hoorakei_temp)
													hoorakei_new_num+=1
													hansuu_temp,string_temp=yaku_and_output(tehai9,hoorakei_temp,did_tsumo,is_karaten,tsumohai,dahai,is_number_only,has_koyaku)
													hansuu.append(hansuu_temp)
													string.append(string_temp)
						continue
					for hai_picked in range(10 if is_number_only else 38):
						if tehai9_temp[hai_picked]==0:
							continue
						elif tehai9_temp[hai_picked]>=3:#kootsu exists
							tehai9_temp[hai_picked]-=3
							hoorakei_temp.append(['k',hai_picked,hai_picked,hai_picked])
							break
						elif hai_picked<28 and all(tehai9_temp[hai_picked:hai_picked+3]):#shuntsu exists
							tehai9_temp[hai_picked]-=1
							tehai9_temp[hai_picked+1]-=1
							tehai9_temp[hai_picked+2]-=1
							hoorakei_temp.append(['s',hai_picked,hai_picked+1,hai_picked+2])
							break
						else:#neither kootsu nor shuntsu exists
							tehai9_temp=None
							break

		if did_tsumo==False and is_hoora:
			is_tenpai=True
			if not is_karaten:
				agarihais.append(tsumohai)
				if max(hansuu)>=13:
					kouten.append(max(hansuu)//13*13)
				else:
					kouten.append(max(hansuu))

		if did_tsumo and not is_hoora:
			if is_beginning_of_the_cosmos:
				string.append(s.hoora+" | 55z 5555z 5555z 5555z 5555z | "+s.beginning_of_the_cosmos+"(140"+s.fuu+"105"+s.han+" 90865195024359483499283685761351700"+s.ten+")"+s.colon+s.tsuuiisoo+s.ideographic_comma+s.sanankoo+s.ideographic_comma+s.suukantsu+s.ideographic_comma+s.rinshankaihou+s.ideographic_comma+s.yakuhai_haku+"4"+s.ideographic_comma+s.dora+"72")
			else:
				string.append(s.not_hoora)
				#dahai
				for sutehai_i in range(10 if is_number_only else 38):
					if sutehai_i in tehai1:
						tehai1_new=tehai1.copy()
						tehai1_new.remove(sutehai_i)
						a,b=InputShonhai(tehai1=tehai1_new,dahai=sutehai_i,is_number_only=is_number_only,has_koyaku=has_koyaku)
						string.append(a)

		if did_tsumo:
			break
		if did_tsumo==False:
			tehai9[tsumohai]-=1

	return string

def CalcScore(fan, fu, isHost, isTsumo):
    if fan <= 4:
        if fan == 4:
            if fu >= 40:
                oriScore = 8000
                if isHost:
                    oriScore = 12000
                return oriScore
        if isTsumo:
            if isHost:
                oriScore = math.ceil(fu * pow(2,fan + 2) * 2 /100)*100 * 3
            else:
                oriScore = math.ceil(fu * pow(2,fan + 2) * 2 /100)*100 + math.ceil(fu * pow(2,fan + 2)/100)*100 * 2
        else:
            if isHost:
                oriScore = math.ceil(fu * pow(2,fan + 2) * 6 /100)*100
            else:
                oriScore = math.ceil(fu * pow(2,fan + 2) * 4 /100)*100

    elif fan >= 5 and fan < 6:
        oriScore = 8000
        if isHost:
            oriScore = 12000
    elif fan >= 6 and fan < 8:
        oriScore = 12000
        if isHost:
            oriScore = 18000
    elif fan >= 8 and fan <= 10:
        oriScore = 16000
        if isHost:
            oriScore = 24000
    elif fan > 10 and fan < 13:
        oriScore = 24000
        if isHost:
            oriScore = 36000
    elif fan >= 13:
        oriScore = 36000
        if isHost:
            oriScore = 48000

    return oriScore