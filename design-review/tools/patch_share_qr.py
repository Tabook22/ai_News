from pathlib import Path

p = Path("app/app.py")
s = p.read_text(encoding="utf-8")

route = '''

@app.route('/share-qr.png')
def share_qr_png():
    """Public QR image for the article share card."""
    from flask import Response
    target = (request.args.get('target') or '').strip()
    if not target.startswith(('http://', 'https://')):
        target = url_for('magazine_view', _external=True)
    try:
        import qrcode
        qr = qrcode.QRCode(border=2, box_size=8, error_correction=qrcode.constants.ERROR_CORRECT_M)
        qr.add_data(target)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0f172a", back_color="#ffffff").convert('RGB')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return Response(buf.getvalue(), mimetype='image/png')
    except ImportError:
        abort(503)

'''
if "def share_qr_png()" not in s:
    anchor = "@app.route('/qr')\n@login_required\ndef qr_page():"
    s = s.replace(anchor, route + anchor, 1)
    print("share QR route added")
p.write_text(s, encoding="utf-8")
