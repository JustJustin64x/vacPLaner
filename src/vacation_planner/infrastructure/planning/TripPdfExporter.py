from pathlib import Path
from xml.sax.saxutils import escape, quoteattr


class TripPdfExporter:
    def export(self, path, sections):
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import reportlab
        font_candidates=[Path('/System/Library/Fonts/Supplemental/Arial.ttf'),
                         Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
                         Path(reportlab.__file__).parent/'fonts/Vera.ttf']
        font=next(p for p in font_candidates if p.exists())
        pdfmetrics.registerFont(TTFont('TravelSans',str(font)))
        styles=getSampleStyleSheet()
        for style in styles.byName.values():
            style.fontName='TravelSans'
        styles['Normal'].fontSize=10
        styles['Normal'].leading=15
        styles['Normal'].spaceAfter=6
        styles['Heading2'].fontSize=14
        styles['Heading2'].leading=18
        styles['Heading2'].spaceBefore=13
        styles['Heading2'].textColor=colors.HexColor('#183f5e')
        styles['Heading2'].keepWithNext=True
        flow=[Paragraph('Meine Überraschungsreise',styles['Title']),Spacer(1,12)]
        for title,paragraphs,links in sections:
            section = []
            section.append(Paragraph(escape(title),styles['Heading2']))
            for paragraph in paragraphs:
                if paragraph:
                    section.append(Paragraph(escape(str(paragraph)).replace('\n','<br/>'),styles['Normal']))
            for label,url in links:
                if url.startswith(('https://','http://')):
                    section.append(Paragraph('<link href='+quoteattr(url)+' color="#176294">'+escape(label)+'</link>',styles['Normal']))
            flow.append(KeepTogether(section))
        def footer(canvas,doc):
            canvas.saveState()
            canvas.setFont('TravelSans',8)
            canvas.setFillColor(colors.HexColor('#4b5563'))
            canvas.drawString(42,26,'Private Reiseplanung · Preise und Verfügbarkeit können sich ändern')
            canvas.drawRightString(A4[0]-42,26,str(doc.page))
            canvas.restoreState()
        doc=SimpleDocTemplate(str(path),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=40,bottomMargin=48,
                              title='Meine Überraschungsreise',author='Lokaler Urlaubsplaner')
        doc.build(flow,onFirstPage=footer,onLaterPages=footer)
