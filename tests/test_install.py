"""Test suite for claif_cod installation functionality."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from claif_cod.install import (
    get_codex_status,
    install_codex,
    is_codex_installed,
    uninstall_codex,
)


class TestInstallCodex:
    """Test suite for install_codex function."""

    @patch("claif_cod.install.ensure_bun_installed")
    def test_install_bun_failure(self, mock_ensure_bun):
        """Test install when bun installation fails."""
        mock_ensure_bun.return_value = False
        
        result = install_codex()
        
        assert result["installed"] == []
        assert result["failed"] == ["codex"]
        assert result["message"] == "bun installation failed"

    @patch("claif_cod.install.ensure_bun_installed")
    @patch("claif_cod.install.get_install_location")
    @patch("claif_cod.install.install_npm_package_globally")
    def test_install_npm_failure(self, mock_npm_install, mock_get_location, mock_ensure_bun):
        """Test install when npm package installation fails."""
        mock_ensure_bun.return_value = True
        mock_get_location.return_value = Path("/tmp/claif/bin")
        mock_npm_install.return_value = False
        
        result = install_codex()
        
        assert result["installed"] == []
        assert result["failed"] == ["codex"]
        assert result["message"] == "@openai/codex installation failed"
        mock_npm_install.assert_called_once_with("@openai/codex")

    @patch("claif_cod.install.ensure_bun_installed")
    @patch("claif_cod.install.get_install_location")
    @patch("claif_cod.install.install_npm_package_globally")
    @patch("claif_cod.install.bundle_all_tools")
    def test_install_bundle_failure(self, mock_bundle, mock_npm_install, mock_get_location, mock_ensure_bun):
        """Test install when bundling fails."""
        mock_ensure_bun.return_value = True
        mock_get_location.return_value = Path("/tmp/claif/bin")
        mock_npm_install.return_value = True
        mock_bundle.return_value = None  # Bundling failed
        
        result = install_codex()
        
        assert result["installed"] == []
        assert result["failed"] == ["codex"]
        assert result["message"] == "bundling failed"

    @patch("claif_cod.install.ensure_bun_installed")
    @patch("claif_cod.install.get_install_location")
    @patch("claif_cod.install.install_npm_package_globally")
    @patch("claif_cod.install.bundle_all_tools")
    @patch("claif_cod.install.shutil.copy2")
    @patch("claif_cod.install.prompt_tool_configuration")
    def test_install_success(self, mock_prompt, mock_copy, mock_bundle, mock_npm_install, 
                           mock_get_location, mock_ensure_bun):
        """Test successful installation."""
        mock_ensure_bun.return_value = True
        mock_get_location.return_value = Path("/tmp/claif/bin")
        mock_npm_install.return_value = True
        
        # Mock bundle directory structure
        dist_dir = Path("/tmp/dist")
        mock_bundle.return_value = dist_dir
        
        # Mock source file exists
        with patch("pathlib.Path.exists") as mock_exists:
            with patch("pathlib.Path.chmod") as mock_chmod:
                mock_exists.return_value = True
                
                result = install_codex()
                
                assert result["installed"] == ["codex"]
                assert result["failed"] == []
                
                # Verify file operations
                mock_copy.assert_called_once()
                source_path, target_path = mock_copy.call_args[0]
                assert str(source_path) == str(dist_dir / "codex" / "codex")
                assert str(target_path) == "/tmp/claif/bin/codex"
                
                # Verify chmod was called
                mock_chmod.assert_called_once_with(0o755)
                
                # Verify configuration prompt
                mock_prompt.assert_called_once_with(
                    "Codex",
                    [
                        "export OPENAI_API_KEY=your_api_key_here",
                        "codex --help",
                    ]
                )

    @patch("claif_cod.install.ensure_bun_installed")
    @patch("claif_cod.install.get_install_location")
    @patch("claif_cod.install.install_npm_package_globally")
    @patch("claif_cod.install.bundle_all_tools")
    def test_install_source_not_found(self, mock_bundle, mock_npm_install, 
                                    mock_get_location, mock_ensure_bun):
        """Test install when bundled source doesn't exist."""
        mock_ensure_bun.return_value = True
        mock_get_location.return_value = Path("/tmp/claif/bin")
        mock_npm_install.return_value = True
        
        dist_dir = Path("/tmp/dist")
        mock_bundle.return_value = dist_dir
        
        # Mock source file doesn't exist
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = False
            
            result = install_codex()
            
            assert result["installed"] == []
            assert result["failed"] == ["codex"]
            assert result["message"] == "bundled executable not found"

    @patch("claif_cod.install.ensure_bun_installed")
    @patch("claif_cod.install.get_install_location")
    @patch("claif_cod.install.install_npm_package_globally")
    @patch("claif_cod.install.bundle_all_tools")
    @patch("claif_cod.install.shutil.copy2")
    def test_install_copy_exception(self, mock_copy, mock_bundle, mock_npm_install,
                                  mock_get_location, mock_ensure_bun):
        """Test install when copy operation fails."""
        mock_ensure_bun.return_value = True
        mock_get_location.return_value = Path("/tmp/claif/bin")
        mock_npm_install.return_value = True
        
        dist_dir = Path("/tmp/dist")
        mock_bundle.return_value = dist_dir
        
        # Mock copy failure
        mock_copy.side_effect = OSError("Permission denied")
        
        with patch("pathlib.Path.exists", return_value=True):
            result = install_codex()
            
            assert result["installed"] == []
            assert result["failed"] == ["codex"]
            assert "installation failed: Permission denied" in result["message"]


class TestUninstallCodex:
    """Test suite for uninstall_codex function."""

    @patch("claif_cod.install.uninstall_tool")
    def test_uninstall_success(self, mock_uninstall):
        """Test successful uninstallation."""
        mock_uninstall.return_value = True
        
        result = uninstall_codex()
        
        assert result["uninstalled"] == ["codex"]
        assert result["failed"] == []
        mock_uninstall.assert_called_once_with("codex")

    @patch("claif_cod.install.uninstall_tool")
    def test_uninstall_failure(self, mock_uninstall):
        """Test failed uninstallation."""
        mock_uninstall.return_value = False
        
        result = uninstall_codex()
        
        assert result["uninstalled"] == []
        assert result["failed"] == ["codex"]
        assert result["message"] == "codex uninstallation failed"


class TestIsCodexInstalled:
    """Test suite for is_codex_installed function."""

    @patch("claif_cod.install.get_install_location")
    def test_installed_as_file(self, mock_get_location):
        """Test when codex is installed as a file."""
        install_dir = Path("/tmp/claif/bin")
        mock_get_location.return_value = install_dir
        
        with patch("pathlib.Path.exists") as mock_exists:
            with patch("pathlib.Path.is_file") as mock_is_file:
                mock_exists.return_value = True
                mock_is_file.return_value = True
                
                assert is_codex_installed() is True

    @patch("claif_cod.install.get_install_location")
    def test_installed_as_directory(self, mock_get_location):
        """Test when codex is installed as a directory."""
        install_dir = Path("/tmp/claif/bin")
        mock_get_location.return_value = install_dir
        
        # First exists() check returns False (not a file), second returns True (is a dir)
        with patch("pathlib.Path.exists", side_effect=[False, True]):
            with patch("pathlib.Path.is_dir", return_value=True):
                assert is_codex_installed() is True

    @patch("claif_cod.install.get_install_location")
    def test_not_installed(self, mock_get_location):
        """Test when codex is not installed."""
        install_dir = Path("/tmp/claif/bin")
        mock_get_location.return_value = install_dir
        
        with patch("pathlib.Path.exists", return_value=False):
            assert is_codex_installed() is False


class TestGetCodexStatus:
    """Test suite for get_codex_status function."""

    @patch("claif_cod.install.is_codex_installed")
    @patch("claif_cod.install.get_install_location")
    def test_status_installed(self, mock_get_location, mock_is_installed):
        """Test status when codex is installed."""
        mock_is_installed.return_value = True
        mock_get_location.return_value = Path("/home/user/.claif/bin")
        
        status = get_codex_status()
        
        assert status["installed"] is True
        assert status["path"] == "/home/user/.claif/bin/codex"
        assert status["type"] == "bundled (claif-owned)"

    @patch("claif_cod.install.is_codex_installed")
    def test_status_not_installed(self, mock_is_installed):
        """Test status when codex is not installed."""
        mock_is_installed.return_value = False
        
        status = get_codex_status()
        
        assert status["installed"] is False
        assert status["path"] is None
        assert status["type"] is None