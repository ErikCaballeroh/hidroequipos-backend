def generate_restock_email(supplier_name: str, product_name: str, product_code: str, quantity: float) -> str:
    return f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Solicitud de Reabastecimiento — Hidroequipos</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #f8fafc;
            color: #0f172a;
            -webkit-font-smoothing: antialiased;
            padding: 40px 16px;
        }}

        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        }}

        /* Header */
        .header {{
            padding: 32px 32px 24px;
            border-bottom: 1px solid #e2e8f0;
        }}

        .header h1 {{
            font-size: 24px;
            font-weight: 600;
            letter-spacing: -0.025em;
            color: #0f172a;
        }}

        .header p {{
            margin-top: 6px;
            font-size: 14px;
            color: #64748b;
        }}

        /* Body */
        .body {{
            padding: 32px;
        }}

        .body p {{
            font-size: 15px;
            line-height: 1.6;
            color: #334155;
            margin-bottom: 24px;
        }}

        /* Data Box */
        .data-box {{
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 24px;
        }}

        .data-row {{
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #e2e8f0;
        }}

        .data-row:last-child {{
            border-bottom: none;
            padding-bottom: 0;
        }}

        .data-row:first-child {{
            padding-top: 0;
        }}

        .data-label {{
            font-size: 14px;
            font-weight: 500;
            color: #64748b;
        }}

        .data-value {{
            font-size: 14px;
            font-weight: 600;
            color: #0f172a;
            text-align: right;
        }}

        /* Footer */
        .footer {{
            background-color: #f8fafc;
            padding: 24px 32px;
            border-top: 1px solid #e2e8f0;
            text-align: center;
        }}

        .footer-brand {{
            font-size: 14px;
            font-weight: 600;
            color: #0f172a;
            margin-bottom: 8px;
        }}

        .footer p {{
            font-size: 12px;
            color: #64748b;
            line-height: 1.5;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Solicitud de Pedido</h1>
            <p>Hidroequipos S.A. de C.V.</p>
        </div>

        <div class="body">
            <p>Hola <strong>{supplier_name}</strong>,</p>
            <p>Por medio de la presente, solicitamos amablemente el reabastecimiento del siguiente producto para nuestro inventario. A continuación los detalles de la solicitud:</p>

            <div class="data-box">
                <div class="data-row">
                    <span class="data-label">Producto</span>
                    <span class="data-value">{product_name}</span>
                </div>
                <div class="data-row">
                    <span class="data-label">Código (SKU)</span>
                    <span class="data-value">{product_code}</span>
                </div>
                <div class="data-row">
                    <span class="data-label">Cantidad solicitada</span>
                    <span class="data-value">{quantity} unidades</span>
                </div>
            </div>

            <p>Favor de confirmar la recepción de este pedido y el tiempo estimado de entrega contestando a este correo.</p>
            <p>Saludos cordiales,<br><strong>El equipo de Hidroequipos</strong></p>
        </div>

        <div class="footer">
            <div class="footer-brand">Hidroequipos</div>
            <p>Este es un mensaje automático generado desde nuestro sistema de inventario.<br>Por favor, confirma el pedido respondiendo a este mensaje.</p>
        </div>
    </div>
</body>
</html>
    """
