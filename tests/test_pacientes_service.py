import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from services import pacientes_service


class PacientesServiceTest(unittest.TestCase):
    def setUp(self):
        self.supabase = MagicMock()

    @patch.object(pacientes_service, "supabase")
    def test_create_paciente(self, mocked_supabase):
        data = {"nombre": "Ana", "dni": "1", "celular": "999", "asistencia": True}
        mocked_supabase.table.return_value.insert.return_value.execute.return_value = SimpleNamespace(data=[data])

        result = pacientes_service.create_paciente(data)

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"], data)
        mocked_supabase.table.assert_called_once_with("pacientes")

    @patch.object(pacientes_service, "supabase")
    def test_list_pacientes_with_limit_and_offset(self, mocked_supabase):
        query = mocked_supabase.table.return_value.select.return_value
        query.range.return_value.execute.return_value = SimpleNamespace(data=[{"id": 1}])

        result = pacientes_service.list_pacientes(limit=10, offset=20)

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"], [{"id": 1}])
        query.range.assert_called_once_with(20, 29)

    def test_create_paciente_rejects_invalid_data(self):
        result = pacientes_service.create_paciente({"nombre": "Ana"})

        self.assertFalse(result["ok"])
        self.assertIn("dni", result["error"])


if __name__ == "__main__":
    unittest.main()