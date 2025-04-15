import yaml
import requests
import time
import os
from collections import defaultdict
# Importing urlparse to refine domain extraction
from urllib.parse import urlparse

# Function to load configuration from the YAML file
def load_config(file_path):

    # Check if the file exists and is a valid YAML file
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Configuration file {file_path} not found.")
    if not os.path.isfile(file_path):
        raise IsADirectoryError(f"Error: Path '{file_path}' is not a file.")
    
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    #Catch any YAML parsing errors
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file: {e}")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {e}")



# Function to perform health checks
def check_health(endpoint):
    url = endpoint['url']
    # Default to GET method if not specified
    method = endpoint.get('method', 'GET')
    headers = endpoint.get('headers')
    body = endpoint.get('body')

    try:
        response = requests.request(method, url, headers=headers, json=body, timeout=5)
        elapsed_time = response.elapsed.total_seconds()
        max_response_time = 0.5 

        if 200 <= response.status_code < 300:
            return "UP"
        else:
            return "DOWN"
    except requests.RequestException:
        return "DOWN"
    except requests.Timeout:
        return "DOWN"
    
    #Catch unexpected errors during request
    except Exception as e:
        print(f"Warning: An error occurred while checking {url}: {e}")
        return "DOWN"

# Main function to monitor endpoints
def monitor_endpoints(file_path):
    config = load_config(file_path)
    domain_stats = defaultdict(lambda: {"up": 0, "total": 0})
    check_interval = 15

    while True:
        start_time = time.time()

        for endpoint in config:
            try:
                parsed_url = urlparse(endpoint["url"])
                domain = parsed_url.hostname
                if domain is None: # Handle cases where parsing might fail or hostname is missing
                   print(f"Warning: Could not parse domain from URL: {endpoint['url']}. Skipping.")
                   continue
            except Exception as e:
                print(f"Warning: Error parsing URL {endpoint['url']}: {e}. Skipping.")
                continue

            result = check_health(endpoint)

            domain_stats[domain]["total"] += 1
            if result == "UP":
                domain_stats[domain]["up"] += 1

        # Log cumulative availability percentages
        for domain, stats in domain_stats.items():
            if stats["total"] > 0:
                availability = round(100 * stats["up"] / stats["total"])
                print(f"{domain} has {availability}% availability percentage")
            else:
                print(f"{domain} has 0 checks recorded.")

        print("---")
        # Sleep for the specified interval, adjusting for execution time
        end_time = time.time()
        elapsed_time = end_time - start_time
        sleep_time = check_interval - elapsed_time
        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            print(f"Warning: Health check took longer than {check_interval} seconds. Adjusting sleep time.")
            pass
# Entry point of the program
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python monitor.py <config_file_path>")
        sys.exit(1)

    config_file = sys.argv[1]
    try:
        monitor_endpoints(config_file)
    except (FileNotFoundError, IsADirectoryError, ValueError, RuntimeError) as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
        sys.exit(0)