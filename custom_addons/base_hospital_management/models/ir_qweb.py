# -*- coding: utf-8 -*-
from odoo import models
from odoo.tools.image import image_data_uri

class IrQWeb(models.AbstractModel):
    _inherit = 'ir.qweb'

    def _get_converted_image_data_uri(self, base64_source):
        """Override to handle cases where base64_source is a string (str).
        This can happen when binary data is serialized to JSON during report
        generation and then passed back to the server.
        """
        if isinstance(base64_source, str):
            # Ensure it's bytes for the core image_data_uri function
            return image_data_uri(base64_source.encode())
        return super()._get_converted_image_data_uri(base64_source)
