import unittest
from unittest.mock import MagicMock, patch
import os
import tempfile

class TestPdfExport(unittest.TestCase):
    def setUp(self):
        self.sample_items = [
            {
                'id': 1,
                'brand': 'Filamentwerk',
                'material': 'PLA',
                'subtype': 'Matte',
                'color': 'Rot (#FF0000)',
                'spool_id': 1,
                'type': 'REGAL',
                'loc_id': 'A1',
                'weight_gross': '1000',
                'capacity': '1000',
                'reorder': False
            },
            {
                'id': 2,
                'brand': 'Prusament',
                'material': 'PETG',
                'subtype': 'Standard',
                'color': 'Blau (#0000FF)',
                'spool_id': 2,
                'type': 'AMS',
                'loc_id': 'Slot 1',
                'weight_gross': '850',
                'capacity': '1000',
                'reorder': False
            }
        ]
        self.spools = [
            {'id': 1, 'name': 'Standard Plastik', 'weight': 200},
            {'id': 2, 'name': 'Standard Pappe', 'weight': 210}
        ]

    @patch("tkinter.filedialog.asksaveasfilename")
    @patch("os.startfile")
    @patch("tkinter.messagebox.askyesno", return_value=False)
    def test_generate_pdf_landscape(self, mock_askyesno, mock_startfile, mock_save_dialog):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name

        mock_save_dialog.return_value = tmp_path

        mock_app = MagicMock()
        mock_app.spools = self.spools
        mock_app.filter_mat_var.get.return_value = "Alle Materialien"
        mock_app.filter_color_var.get.return_value = "Alle Farben"
        mock_app.filter_loc_var.get.return_value = "Alle Orte"
        mock_app.filter_brand_var.get.return_value = "Alle Hersteller"
        mock_app.search_var.get.return_value = ""
        mock_app.settings = {}

        selected_cols = ["id", "brand", "material", "color", "net_weight"]

        from filament_gui import FilamentApp
        FilamentApp.generate_pdf_file(mock_app, self.sample_items, selected_cols, orientation="landscape")

        self.assertTrue(os.path.exists(tmp_path))
        self.assertGreater(os.path.getsize(tmp_path), 0)

        # Cleanup
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    @patch("tkinter.filedialog.asksaveasfilename")
    @patch("os.startfile")
    @patch("tkinter.messagebox.askyesno", return_value=False)
    def test_generate_pdf_portrait(self, mock_askyesno, mock_startfile, mock_save_dialog):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name

        mock_save_dialog.return_value = tmp_path

        mock_app = MagicMock()
        mock_app.spools = self.spools
        mock_app.filter_mat_var.get.return_value = "Alle Materialien"
        mock_app.filter_color_var.get.return_value = "Alle Farben"
        mock_app.filter_loc_var.get.return_value = "Alle Orte"
        mock_app.filter_brand_var.get.return_value = "Alle Hersteller"
        mock_app.search_var.get.return_value = ""
        mock_app.settings = {}

        selected_cols = ["id", "brand", "material", "net_weight"]

        from filament_gui import FilamentApp
        FilamentApp.generate_pdf_file(mock_app, self.sample_items, selected_cols, orientation="portrait")

        self.assertTrue(os.path.exists(tmp_path))
        self.assertGreater(os.path.getsize(tmp_path), 0)

        # Cleanup
        try:
            os.remove(tmp_path)
        except OSError:
            pass

if __name__ == '__main__':
    unittest.main()
