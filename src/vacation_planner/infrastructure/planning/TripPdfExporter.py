from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

from .PdfTripPresenter import PdfTripPresenter

NAVY, BLUE, SKY, INK, MUTED, RED = '#17324D', '#1E6A78', '#DDEFF1', '#263238', '#5C6B73', '#9A3D36'


class MapFlowable:
    def __new__(cls, points, width, height=190):
        from reportlab.platypus import Flowable
        from reportlab.lib import colors
        class Map(Flowable):
            def __init__(self): super().__init__(); self.width=width; self.height=height
            def draw(self):
                c=self.canv; c.saveState(); c.setFillColor(colors.HexColor('#F2F7F5')); c.roundRect(0,0,self.width,self.height,8,fill=1,stroke=0)
                if not points:
                    c.setFillColor(colors.HexColor(MUTED)); c.setFont('TravelSans',10); c.drawCentredString(self.width/2,self.height/2,'Keine belegten Koordinaten für eine Übersichtskarte'); c.restoreState(); return
                lats=[float(p['latitude']) for p in points]; lons=[float(p['longitude']) for p in points]
                minlat,maxlat=min(lats),max(lats); minlon,maxlon=min(lons),max(lons); plot_w=self.width*.58; pad=20
                spanlat=max(maxlat-minlat,.01); spanlon=max(maxlon-minlon,.01)
                c.setStrokeColor(colors.HexColor('#B5CBC7')); c.setLineWidth(.5)
                for i in range(1,5):
                    x=pad+(plot_w-2*pad)*i/5; y=pad+(self.height-2*pad)*i/5; c.line(x,pad,x,self.height-pad); c.line(pad,y,plot_w-pad,y)
                palette={'destination':'#17324D','lodging':'#D97706','activity':'#1E6A78','transport':'#7C3AED'}
                for index,p in enumerate(points,1):
                    x=pad+(float(p['longitude'])-minlon)/spanlon*(plot_w-2*pad); y=pad+(float(p['latitude'])-minlat)/spanlat*(self.height-2*pad)
                    c.setFillColor(colors.HexColor(palette.get(p['kind'],BLUE))); c.circle(x,y,7,fill=1,stroke=0); c.setFillColor(colors.white); c.setFont('TravelSans-Bold',7); c.drawCentredString(x,y-2.5,str(index))
                lx=plot_w+8; c.setFillColor(colors.HexColor(INK)); c.setFont('TravelSans-Bold',8); c.drawString(lx,self.height-17,'Legende')
                for index,p in enumerate(points[:10],1):
                    y=self.height-32-(index-1)*15; c.setFillColor(colors.HexColor(palette.get(p['kind'],BLUE))); c.circle(lx+4,y+2,5,fill=1,stroke=0); c.setFillColor(colors.white); c.setFont('TravelSans-Bold',6); c.drawCentredString(lx+4,y,str(index)); c.setFillColor(colors.HexColor(INK)); c.setFont('TravelSans',7.5); c.drawString(lx+13,y-1,(p['name'][:31]+'…') if len(p['name'])>32 else p['name'])
                c.setFillColor(colors.HexColor(MUTED)); c.setFont('TravelSans',6.8); c.drawString(pad,6,'Schematische geografische Übersicht · keine Straßenkarte oder Route'); c.restoreState()
        return Map()


class TripPdfExporter:
    def export(self, path, sections):
        """Compatibility export for existing callers."""
        self._setup()
        from reportlab.platypus import Spacer
        story=[self._heading('Meine Überraschungsreise',0,'legacy')]
        for title,paragraphs,links in sections:
            story.append(self._heading(title,1,'legacy-'+str(len(story))))
            story.extend(self._paragraph(escape(str(x)).replace('\n','<br/>')) for x in paragraphs if x)
            story.extend(self._link(label,url) for label,url in links if url.startswith(('http://','https://'))); story.append(Spacer(1,6))
        self._build(path,story,'Meine Überraschungsreise')

    def export_trips(self, path, trips, title='Unsere Reiseideen'):
        if not trips: raise ValueError('Mindestens eine Reise muss ausgewählt sein.')
        self._setup(); models=[PdfTripPresenter.present(x) for x in trips]; story=self._cover(models,title)
        if len(models)>1: story += self._toc()+self._comparison(models)
        for index,model in enumerate(models): story += self._trip(model,index)
        self._build(path,story,title)

    def _setup(self):
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        import reportlab
        regular=next(p for p in (Path('/System/Library/Fonts/Supplemental/Arial.ttf'),Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),Path(reportlab.__file__).parent/'fonts/Vera.ttf') if p.exists())
        bold=next((p for p in (Path('/System/Library/Fonts/Supplemental/Arial Bold.ttf'),Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),Path(reportlab.__file__).parent/'fonts/VeraBd.ttf') if p.exists()),regular)
        for name,path in [('TravelSans',regular),('TravelSans-Bold',bold)]:
            if name not in pdfmetrics.getRegisteredFontNames(): pdfmetrics.registerFont(TTFont(name,str(path)))
        styles=getSampleStyleSheet()
        styles.add(ParagraphStyle(name='TravelBody',parent=styles['BodyText'],fontName='TravelSans',fontSize=10.8,leading=15.2,textColor=colors.HexColor(INK),spaceAfter=7))
        styles.add(ParagraphStyle(name='TravelSmall',parent=styles['TravelBody'],fontSize=8.5,leading=11.5,textColor=colors.HexColor(MUTED),spaceAfter=4))
        styles.add(ParagraphStyle(name='TravelH1',parent=styles['Heading1'],fontName='TravelSans-Bold',fontSize=23,leading=27,textColor=colors.HexColor(NAVY),spaceBefore=8,spaceAfter=12,keepWithNext=True))
        styles.add(ParagraphStyle(name='TravelH2',parent=styles['Heading2'],fontName='TravelSans-Bold',fontSize=15,leading=19,textColor=colors.HexColor(BLUE),spaceBefore=14,spaceAfter=8,keepWithNext=True))
        styles.add(ParagraphStyle(name='TravelH3',parent=styles['Heading3'],fontName='TravelSans-Bold',fontSize=11.5,leading=14,textColor=colors.HexColor(NAVY),spaceBefore=8,spaceAfter=5,keepWithNext=True))
        styles.add(ParagraphStyle(name='TravelCard',parent=styles['TravelBody'],fontSize=9.5,leading=13,spaceAfter=3))
        styles.add(ParagraphStyle(name='TravelLink',parent=styles['TravelBody'],fontSize=9.3,textColor=colors.HexColor(BLUE),spaceAfter=3))
        self.styles=styles

    def _build(self,path,story,title):
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.platypus import BaseDocTemplate,Frame,PageTemplate
        from reportlab.lib import colors
        class Document(BaseDocTemplate):
            def afterFlowable(doc,flowable):
                key=getattr(flowable,'_bookmark_key',None); level=getattr(flowable,'_outline_level',0); heading=getattr(flowable,'_bookmark_title',None)
                if key and heading:
                    doc.canv.bookmarkPage(key); doc.canv.addOutlineEntry(heading,key,level=level,closed=False)
                    if getattr(flowable,'_toc',False): doc.notify('TOCEntry',(level,heading,doc.page,key))
        out=Path(path);out.parent.mkdir(parents=True,exist_ok=True)
        doc=Document(str(out),pagesize=A4,leftMargin=17*mm,rightMargin=17*mm,topMargin=17*mm,bottomMargin=18*mm,title=title,author='Lokaler Urlaubsplaner',subject='Private Reiseplanung und Reisevergleich',creator='vacPLaner')
        frame=Frame(doc.leftMargin,doc.bottomMargin,doc.width,doc.height,id='main')
        def page(canvas,document):
            canvas.saveState();canvas.setFont('TravelSans',8);canvas.setFillColor(colors.HexColor(MUTED));canvas.drawString(doc.leftMargin,9*mm,'vacPLaner · private Reiseübersicht');canvas.drawRightString(A4[0]-doc.rightMargin,9*mm,f'Seite {document.page}');canvas.setStrokeColor(colors.HexColor('#D9E3E5'));canvas.line(doc.leftMargin,13*mm,A4[0]-doc.rightMargin,13*mm);canvas.restoreState()
        doc.addPageTemplates([PageTemplate(id='travel',frames=[frame],onPage=page)]);doc.multiBuild(story)

    def _cover(self,models,title):
        from reportlab.platypus import Spacer,PageBreak,Table,TableStyle,Paragraph
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        names=' · '.join(m['name'] for m in models)
        box=Table([[self._paragraph('REISEFÜHRER & ENTSCHEIDUNGSHILFE','TravelSmall')],[Paragraph(escape(title),self.styles['TravelH1'])],[self._paragraph(escape(names))],[self._paragraph(f"{len(models)} Reiseidee{'n' if len(models)!=1 else ''} · aus gespeicherten Quellenständen",'TravelSmall')]],colWidths=[165*mm],hAlign='LEFT')
        box.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor(SKY)),('BOX',(0,0),(-1,-1),0,colors.HexColor(SKY)),('LEFTPADDING',(0,0),(-1,-1),12*mm),('RIGHTPADDING',(0,0),(-1,-1),12*mm),('TOPPADDING',(0,0),(-1,-1),8*mm),('BOTTOMPADDING',(0,0),(-1,-1),8*mm)]))
        result=[Spacer(1,22*mm),box,Spacer(1,10*mm)]; result += self._snapshot(models[0]) if len(models)==1 else []; result.append(PageBreak()); return result

    def _toc(self):
        from reportlab.platypus import PageBreak
        from reportlab.platypus.tableofcontents import TableOfContents
        toc=TableOfContents();toc.levelStyles=[self.styles['TravelBody'],self.styles['TravelSmall']]
        return [self._heading('Inhalt',0,'inhalt',False),toc,PageBreak()]

    def _comparison(self,models):
        from reportlab.platypus import Table,TableStyle,PageBreak
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        data=[[self._paragraph('Reiseziel','TravelSmall'),self._paragraph('Rahmen','TravelSmall'),self._paragraph('Vorschlag & Kosten','TravelSmall')]]
        for m in models:
            issues='; '.join(m['issues'][:2]) or 'Keine wesentlichen Lücken erkannt'
            data.append([self._paragraph(f"<b>{escape(m['name'])}</b><br/>{escape(m['country'])}",'TravelCard'),self._paragraph(f"{m['period']}<br/>{m['nights']} Nächte · {m['adults']} Erwachsene<br/>{escape(', '.join(m['interests']) or 'offene Suche')}",'TravelCard'),self._paragraph(f"{escape(m['lodging']['name'] if m['lodging'] else 'Unterkunft offen')}<br/>{escape(m['transport']['mode'] if m['transport'] else 'Anreise offen')} · {escape(m['transport']['time'] if m['transport'] else 'Zeit offen')}<br/><b>{escape(m['cost']['group'])}</b><br/><font color='{RED}'>{escape(issues)}</font>",'TravelCard')])
        table=Table(data,colWidths=[43*mm,55*mm,67*mm],repeatRows=1)
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor(NAVY)),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#C7D4D7')),('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F4F8F8')]),('PADDING',(0,0),(-1,-1),6)]))
        return [self._heading('Reisen vergleichen',0,'vergleich'),table,PageBreak()]

    def _trip(self,m,index):
        from reportlab.platypus import PageBreak,Spacer,KeepTogether
        from reportlab.lib.units import mm
        key='reise-'+str(index+1); story=[self._heading(m['name']+((', '+m['country']) if m['country'] else ''),0,key)]
        image=self._safe_image(m['hero_image']['cache_path'],165*mm,55*mm) if m['hero_image'] else None
        if image: story += [image,Spacer(1,5)]
        if not m['complete']: story.append(self._notice('Unvollständige Reiseidee',' · '.join(m['issues'])))
        story += self._snapshot(m)+[self._heading('Übersichtskarte',1,key+'-karte'),MapFlowable(m['map_points'],165*mm),Spacer(1,4)]
        for point in m['map_points']:
            if point['url']: story.append(self._link('Auf Karte öffnen: '+point['name'],point['url']))
        story.append(PageBreak())
        story.append(self._heading('Anreise vergleichen',1,key+'-anreise'))
        story.append(self._paragraph('Für alle Optionen: '+escape(m['period'])+'. Hin- und Rückreise für '+str(m['adults'])+' Erwachsene. Nicht geprüfte Möglichkeiten bleiben offen.','TravelCard'))
        story.append(self._transport_comparison(m))
        story.append(self._heading('Unterkunft plus Anreise: getrennte Szenarien',2,key+'-szenarien'))
        story.append(self._scenario_comparison(m))
        story.append(self._paragraph('Die Szenarien sind Alternativen und werden nicht addiert. Aktivitäten und Verpflegung bleiben außerhalb des Hauptbudgets. Unvollständige Teilsummen begründen keinen Preissieger.','TravelSmall'))
        if not m['transports']: story.append(self._paragraph('Für diese Reise sind noch keine Anreiseoptionen gespeichert.'))
        for t in m['transports']:
            known=', '.join(x['label']+': '+x['value'] for x in t['known_costs']) or 'Keine Anreisekosten beziffert'; open_text=', '.join(t['open_costs']) or 'keine weiteren offenen Kosten erfasst'
            price_stamp=('Preisstand: '+t.get('retrieved_at','offen')+' · '+t['status']) if t.get('connections') else t['status']
            story.append(self._card(t['mode'],f"Reisezeit je Richtung: {t['time']}<br/>{escape(known)}<br/>{escape(price_stamp)}<br/><font color='{RED}'>Offen: {escape(open_text)}</font>"))
            if t['car_details']:story.append(self._paragraph(escape(t['car_details']),'TravelCard'))
            for direction,leg in zip(('Hinweg','Rückweg'),t['route_legs']):story.append(self._paragraph(direction+': '+escape(leg['distance']+' · '+leg['time']+' reine Fahrzeit'),'TravelCard'))
            for note in t['notes']:story.append(self._paragraph(escape(note),'TravelSmall'))
            for connection in t.get('connections',[]):
                story.append(self._paragraph(escape(connection['from']+' → '+connection['to'])+'<br/>'+escape(connection['departure']+' bis '+connection['arrival'])+'<br/>'+escape(connection['time']+' · '+str(connection['transfers'])+' Umstiege · Preisstand '+t['retrieved_at']),'TravelCard'))
            for link in t['links']: story.append(self._link(link.get('label','Verbindung öffnen'),link['url']))
        lodging_heading=self._heading('Unterkünfte',1,key+'-unterkunft')
        if not m['lodgings']: story += [lodging_heading,self._notice('Unterkunft offen','Es wurde keine eindeutig zugeordnete Unterkunft gespeichert.')]
        for idx,l in enumerate(m['lodgings']):
            title=('Vorgeschlagene Unterkunft · ' if idx==0 else 'Alternative · ')+l['name']; lines=[l['type'],l['address'],l['distance'],l['occupancy'],'Preis für Gruppe und Aufenthalt: '+l['price']]
            if l.get('included'):lines += ['Enthalten: '+'; '.join(l['included']),'Preisstand: '+l.get('retrieved_at','offen')+' · '+l['price_status']]
            if l['amenities']: lines.append('Belegte Ausstattung: '+', '.join(l['amenities']))
            if l['open']: lines.append('Offen: '+'; '.join(l['open']))
            block=([lodging_heading] if idx==0 else [])+[self._heading(title,2,key+'-hotel-'+str(idx)),self._paragraph('<br/>'.join(escape(x) for x in lines if x),'TravelCard')]
            image=self._safe_image(l['image']['cache_path'],72*mm,42*mm) if l['image'] else None
            if image:block.append(image)
            if l['url']:block.append(self._link('Mehr zur Unterkunft',l['url']))
            if l['map_url']:block.append(self._link('Auf Karte öffnen',l['map_url']))
            story.append(KeepTogether(block))
        story.append(self._heading('Aktivitäten nach Interessen',1,key+'-aktivitaeten'))
        if not m['activities']:story.append(self._paragraph('Es sind keine ausreichend konkreten Aktivitäten gespeichert.'))
        for a in m['activities']:
            details=' · '.join(x for x in (', '.join(a['topics']),a['distance'],a['duration'],a['price']) if x);story.append(self._card(a['name'],escape(a['description'])+'<br/><font color="'+MUTED+'">'+escape(details)+'</font>'))
            if a['url']:story.append(self._link('Mehr erfahren',a['url']))
            if a['map_url']:story.append(self._link('Auf Karte öffnen',a['map_url']))
        story.append(self._heading('Offene Planungspunkte & Quellen',1,key+'-quellen'));story.append(self._paragraph(('Datenstand: '+m['researched_at']+'. ')+('Wesentliche offene Angaben: '+'; '.join(m['issues']) if m['issues'] else 'Keine wesentlichen Lücken erkannt.')))
        if m.get('offer_statuses'):
            from ...core.planning.TravelOffers import STATUS_LABELS
            for status in m['offer_statuses']:
                story.append(self._paragraph(escape(status['category']+' · '+status['provider']+': '+STATUS_LABELS[status['status']]+'. '+status['message']),'TravelSmall'))
        for source in m['sources']:story.append(self._link(source.get('label','Quelle')+((' · '+source['credit']) if source.get('credit') else ''),source['url']))
        story.append(self._paragraph('Kartenlinks und Koordinaten: © OpenStreetMap-Mitwirkende (ODbL). Die Übersicht ist schematisch und zeigt keine Straßenroute. Preise und Verfügbarkeit können sich ändern.','TravelSmall'));story.append(PageBreak());return story

    def _comparison_table(self,headers,rows,widths):
        from reportlab.platypus import Table,TableStyle
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        cells=[[self._paragraph('<b>'+escape(h)+'</b>','TravelCard') for h in headers]]
        cells += [[self._paragraph(escape(str(c)).replace('\n','<br/>'),'TravelCard') for c in row] for row in rows]
        table=Table(cells,colWidths=[w*mm for w in widths],repeatRows=1,hAlign='LEFT')
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DCE6E8')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#BFD0D3')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
        return table

    def _transport_comparison(self,m):
        rows=[]
        for c in m['comparisons']:
            rows.append([c['mode'],c['time']+' je Richtung\n'+c['time_note'],
                         'Gruppe: '+c['group']+'\nPro Person: '+c['person'],
                         c['status']+'\nStand: '+c['stamp']+'\nEnthalten: '+('; '.join(c['included']) or 'Leistungsumfang offen')+'\nOffen: '+('; '.join(c['missing']) or 'keine weiteren Kosten erfasst')])
        return self._comparison_table(['Anreise','Zeit bis zum Ziel','Hin- und Rückreise','Leistungen und Preisstatus'],rows,[23,43,43,56])

    def _scenario_comparison(self,m):
        return self._comparison_table(['Unterkunft plus','Gruppe / pro Person','Budget und fehlende Kosten'],
            [[c['mode'],c['scenario_group']+'\n'+c['scenario_person']+' pro Person',c['budget']+'\nOffen: '+('; '.join(c['scenario_missing']) or 'keine weiteren Pflichtkosten erfasst')] for c in m['comparisons']],[28,57,80])

    def _snapshot(self,m):
        from reportlab.platypus import Table,TableStyle
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        rows=[[self._paragraph('<b>Zeitraum</b><br/>'+escape(m['period']),'TravelCard'),self._paragraph(f"<b>Reisegruppe</b><br/>{m['adults']} Erwachsene · {m['rooms']} Zimmer",'TravelCard')],[self._paragraph('<b>Unterkunft</b><br/>'+escape(m['lodging']['name'] if m['lodging'] else 'offen'),'TravelCard'),self._paragraph('<b>Anreise</b><br/>'+escape((m['transport']['mode']+' · '+m['transport']['time']) if m['transport'] else 'offen'),'TravelCard')],[self._paragraph('<b>'+escape(m['cost']['title'])+'</b><br/>Gruppe: '+escape(m['cost']['group'])+'<br/>Rechnerisch pro Person: '+escape(m['cost']['per_person']),'TravelCard'),self._paragraph('<b>Passt zu</b><br/>'+escape(', '.join(m['interests']) or 'offene Suche'),'TravelCard')]]
        t=Table(rows,colWidths=[82.5*mm,82.5*mm]);t.setStyle(TableStyle([('BOX',(0,0),(-1,-1),.5,colors.HexColor('#BFD0D3')),('INNERGRID',(0,0),(-1,-1),.5,colors.HexColor('#DCE6E8')),('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#F7FAFA')),('VALIGN',(0,0),(-1,-1),'TOP'),('PADDING',(0,0),(-1,-1),8)]));return [t]

    def _heading(self,text,level,key,toc=True):
        from reportlab.platypus import Paragraph
        p=Paragraph(f'<a name={quoteattr(key)}/>{escape(text)}',self.styles['TravelH1' if level==0 else 'TravelH2' if level==1 else 'TravelH3']);p._outline_level=level;p._bookmark_key=key;p._bookmark_title=text;p._toc=toc;return p
    def _paragraph(self,text,style='TravelBody'):
        from reportlab.platypus import Paragraph
        return Paragraph(str(text),self.styles[style])
    def _link(self,label,url):return self._paragraph('<link href='+quoteattr(url)+' color="'+BLUE+'">'+escape(label)+'</link>','TravelLink')
    def _card(self,title,body):return self._box('<b>'+escape(title)+'</b><br/>'+body,'#F7FAFA','#C7D4D7')
    def _notice(self,title,text):return self._box('<b>'+escape(title)+'</b><br/>'+escape(text),'#FCEDEA','#D99A91')
    def _box(self,text,background,border):
        from reportlab.platypus import Table,TableStyle
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        t=Table([[self._paragraph(text,'TravelCard')]],colWidths=[165*mm]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor(background)),('BOX',(0,0),(-1,-1),.6,colors.HexColor(border)),('PADDING',(0,0),(-1,-1),8)]));return t
    def _safe_image(self,path,max_width,max_height):
        from reportlab.platypus import Image
        try:
            image=Image(str(path));scale=min(max_width/image.imageWidth,max_height/image.imageHeight);image.drawWidth=image.imageWidth*scale;image.drawHeight=image.imageHeight*scale;return image
        except (OSError,ValueError,TypeError):return None
