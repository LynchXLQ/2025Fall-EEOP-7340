"""
Common utility functions for EEOP notebook tutorials.
"""

import docker
import requests
import time
import json
from typing import Optional, Dict, List, Any
from requests.auth import HTTPBasicAuth


class StatusIndicators:
    """Console status indicators for consistent output formatting."""
    SUCCESS = "[SUCCESS]"
    ERROR = "[ERROR]"
    WARNING = "[WARNING]"
    INFO = "[INFO]"
    WORKING = "[WORKING]"


def print_status(message: str, status: str = StatusIndicators.INFO, details: Optional[str] = None):
    """Print formatted status message with indicator."""
    print(f"{status} {message}")
    if details:
        print(f"  {details}")


def print_raw_response(response: requests.Response, label: str = "Response"):
    """Print raw HTTP response in clean format."""
    print(f"{label}:")
    print(f"  Status: {response.status_code}")
    print(f"  Headers: {dict(response.headers)}")
    if response.text:
        try:
            # Try to format JSON
            data = response.json()
            print(f"  Body: {json.dumps(data, indent=2)}")
        except:
            # Fall back to raw text
            print(f"  Body: {response.text}")
    else:
        print(f"  Body: (empty)")


def print_section(title: str, width: int = 60):
    """Print formatted section header."""
    print(f"\n{'=' * width}")
    print(f"{title}")
    print(f"{'=' * width}")


def format_json_response(data: Dict[str, Any], max_depth: int = 2) -> str:
    """Format JSON response for display with limited depth."""
    if max_depth <= 0:
        return str(data)

    def truncate_dict(obj, depth):
        if depth <= 0:
            return "..."
        if isinstance(obj, dict):
            return {k: truncate_dict(v, depth - 1) for k, v in list(obj.items())[:3]}
        elif isinstance(obj, list):
            return [truncate_dict(item, depth - 1) for item in obj[:3]]
        return obj

    truncated = truncate_dict(data, max_depth)
    return json.dumps(truncated, indent=2)


class DockerHelper:
    """Helper class for Docker operations with consistent error handling."""

    def __init__(self):
        try:
            self.client = docker.from_env()
            print_status("Docker client initialized", StatusIndicators.SUCCESS)
        except Exception as e:
            print_status("Failed to initialize Docker client", StatusIndicators.ERROR, str(e))
            raise

    def get_container_ip(self, container_name: str, network_name: str) -> Optional[str]:
        """Get container IP address with error handling."""
        try:
            container = self.client.containers.get(container_name)
            network_info = container.attrs['NetworkSettings']['Networks']
            if network_name in network_info:
                ip = network_info[network_name]['IPAddress']
                print_status(f"Container {container_name} IP: {ip}", StatusIndicators.SUCCESS)
                return ip
            else:
                print_status(f"Container {container_name} not in network {network_name}", StatusIndicators.WARNING)
                return None
        except docker.errors.NotFound:
            print_status(f"Container {container_name} not found", StatusIndicators.ERROR)
            return None
        except Exception as e:
            print_status(f"Error getting IP for {container_name}", StatusIndicators.ERROR, str(e))
            return None

    def wait_for_container(self, container_name: str, ready_messages: List[bytes],
                           timeout: int = 60, check_interval: int = 2) -> bool:
        """Wait for container to be ready with progress indicators."""
        try:
            container = self.client.containers.get(container_name)
            start_time = time.time()

            print_status(f"Waiting for {container_name} to start (timeout: {timeout}s)", StatusIndicators.WORKING)

            while time.time() - start_time < timeout:
                logs = container.logs()

                for ready_msg in ready_messages:
                    if ready_msg in logs:
                        print_status(f"{container_name} is ready", StatusIndicators.SUCCESS)
                        return True

                elapsed = int(time.time() - start_time)
                if elapsed % 10 == 0:  # Progress update every 10 seconds
                    print_status(f"Still waiting... ({elapsed}s elapsed)", StatusIndicators.WORKING)

                time.sleep(check_interval)

            print_status(f"{container_name} did not start within {timeout}s", StatusIndicators.ERROR)
            return False

        except docker.errors.NotFound:
            print_status(f"Container {container_name} not found", StatusIndicators.ERROR)
            return False
        except Exception as e:
            print_status(f"Error waiting for {container_name}", StatusIndicators.ERROR, str(e))
            return False

    def get_network_containers(self, network_name: str) -> List[Dict[str, str]]:
        """Get all containers in a network with error handling."""
        try:
            network = self.client.networks.get(network_name)
            network_info = self.client.api.inspect_network(network.id)
            containers = network_info.get('Containers', {})

            result = []
            for container_id, container_info in containers.items():
                result.append({
                    'name': container_info.get('Name', 'Unknown'),
                    'ip': container_info.get('IPv4Address', 'Unknown').split('/')[0],
                    'id': container_id
                })

            print_status(f"Found {len(result)} containers in {network_name}", StatusIndicators.SUCCESS)
            return result

        except docker.errors.NotFound:
            print_status(f"Network {network_name} not found", StatusIndicators.ERROR)
            return []
        except Exception as e:
            print_status(f"Error getting network containers", StatusIndicators.ERROR, str(e))
            return []


class RESTClient:
    """Simplified REST client with consistent error handling and timeout."""

    def __init__(self, base_url: str, username: str = "admin", password: str = "admin",
                 timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, password)
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

        # Disable SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def get(self, endpoint: str, show_details: bool = False) -> Optional[requests.Response]:
        """Perform GET request with error handling."""
        url = f"{self.base_url}{endpoint}"

        if show_details:
            print_status(f"GET {endpoint}", StatusIndicators.INFO)

        try:
            response = self.session.get(url, timeout=self.timeout)

            if show_details:
                print_raw_response(response, "GET Response")

            return response

        except requests.exceptions.Timeout:
            print_status(f"GET request timed out ({self.timeout}s)", StatusIndicators.ERROR)
            return None
        except requests.exceptions.RequestException as e:
            print_status(f"GET request failed", StatusIndicators.ERROR, str(e))
            return None

    def post(self, endpoint: str, data: Dict[str, Any], show_details: bool = False) -> Optional[requests.Response]:
        """Perform POST request with error handling."""
        url = f"{self.base_url}{endpoint}"

        if show_details:
            print_status(f"POST {endpoint}", StatusIndicators.INFO)
            print(f"Payload: {json.dumps(data, indent=2)}")

        try:
            response = self.session.post(url, json=data, timeout=self.timeout)

            if show_details:
                print_raw_response(response, "POST Response")

            return response

        except requests.exceptions.Timeout:
            print_status(f"POST request timed out ({self.timeout}s)", StatusIndicators.ERROR)
            return None
        except requests.exceptions.RequestException as e:
            print_status(f"POST request failed", StatusIndicators.ERROR, str(e))
            return None

    def put(self, endpoint: str, data: Dict[str, Any], show_details: bool = False) -> Optional[requests.Response]:
        """Perform PUT request with error handling."""
        url = f"{self.base_url}{endpoint}"

        if show_details:
            print_status(f"PUT {endpoint}", StatusIndicators.INFO)
            print(f"Payload: {json.dumps(data, indent=2)}")

        try:
            response = self.session.put(url, json=data, timeout=self.timeout)

            if show_details:
                print_raw_response(response, "PUT Response")

            return response

        except requests.exceptions.Timeout:
            print_status(f"PUT request timed out ({self.timeout}s)", StatusIndicators.ERROR)
            return None
        except requests.exceptions.RequestException as e:
            print_status(f"PUT request failed", StatusIndicators.ERROR, str(e))
            return None


def wait_with_timeout(condition_func, timeout: int = 60, check_interval: int = 5,
                      description: str = "operation") -> bool:
    """Wait for a condition with timeout and progress indicators."""
    start_time = time.time()

    print_status(f"Waiting for {description} (timeout: {timeout}s)", StatusIndicators.WORKING)

    while time.time() - start_time < timeout:
        if condition_func():
            print_status(f"{description} completed", StatusIndicators.SUCCESS)
            return True

        elapsed = int(time.time() - start_time)
        if elapsed % 15 == 0 and elapsed > 0:  # Progress update every 15 seconds
            print_status(f"Still waiting for {description}... ({elapsed}s)", StatusIndicators.WORKING)

        time.sleep(check_interval)

    print_status(f"{description} timed out after {timeout}s", StatusIndicators.ERROR)
    return False


def validate_prerequisites(required_containers: List[str], network_name: str,
                           docker_helper: DockerHelper) -> bool:
    """Validate that required containers and network exist."""
    print_section("Prerequisites Check")

    # Check network
    try:
        docker_helper.client.networks.get(network_name)
        print_status(f"Network {network_name} exists", StatusIndicators.SUCCESS)
    except docker.errors.NotFound:
        print_status(f"Network {network_name} not found", StatusIndicators.ERROR)
        return False

    # Check containers
    missing_containers = []
    for container_name in required_containers:
        try:
            container = docker_helper.client.containers.get(container_name)
            if container.status == 'running':
                print_status(f"Container {container_name} running", StatusIndicators.SUCCESS)
            else:
                print_status(f"Container {container_name} not running ({container.status})", StatusIndicators.WARNING)
        except docker.errors.NotFound:
            missing_containers.append(container_name)
            print_status(f"Container {container_name} not found", StatusIndicators.ERROR)

    if missing_containers:
        print_status(f"Missing containers: {', '.join(missing_containers)}", StatusIndicators.ERROR)
        return False

    print_status("All prerequisites satisfied", StatusIndicators.SUCCESS)
    return True


def retry_operation(operation_func, max_retries: int = 3, delay: int = 2,
                    description: str = "operation") -> Any:
    """Retry an operation with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return operation_func()
        except Exception as e:
            if attempt == max_retries - 1:
                print_status(f"{description} failed after {max_retries} attempts",
                             StatusIndicators.ERROR, str(e))
                raise

            wait_time = delay * (2 ** attempt)
            print_status(f"{description} attempt {attempt + 1} failed, retrying in {wait_time}s",
                         StatusIndicators.WARNING)
            time.sleep(wait_time)
