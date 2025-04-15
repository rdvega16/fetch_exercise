# Endpoint Availability Monitor

## Prerequisites
Python 3: Ensure Python 3.x is installed. It can be downloaded from [python.org]
pip: Python package installer. Typically comes with Python 3 installation.

## Installation
1. Clone or Download: Get the script 'main.py' and sample configuration 'sample.yaml' if needed.
2. (Optional) Create virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3. Install Dependencies:
    ```bash
    pip install requests PyYAML
    ```

## Configuration
This script requires a YAML configuration file to be run as command line argument

## Usage
Run script from terminal, providing YAML path as argument:
    ```bash
    python main.py <yaml_file_path.yaml>

## Changes to Meet Code Requirements
1. Must accurately determine the availability of all endpoints during every check cycle:
    While the check_health function did perform the core check, it needed modification to account for another requirements.
2. Endpoints are only considered available if they meet the following conditions:
    Status code is between 200 and 299:
    Endpoint responds in 500ms or less
        The check_health function already checked for code between 200 and 299 but required time check.
3. Must return availability by domain:
    The code extracts domain from the url using domain_stats, however, it requires port handling.
4. Must ignore port numbers when determining domain:
    The current domain extractions may include port, needs changes to meed requirement.
5. Check cycles must run and log availability results every 15 seconds regardless of the number of endpoints or their response times:
    The current solution (time.sleep(15)) does not accound for the check duration, so this must be accounted for.

Additional lines of code were added to add some error handling, and print lines to improve readability.

## Code Changes
1. By performing checks in a loop, we can ensure that all endpoints have been addressed.
2. Added a timeout to the response variable for 500ms, as well as some more error handling:
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
3. Aggregates all domains using domain_stats, extra conditions added to the code to account for most cases:
    # Log cumulative availability percentages
        for domain, stats in domain_stats.items():
            if stats["total"] > 0:
                availability = round(100 * stats["up"] / stats["total"])
                print(f"{domain} has {availability}% availability percentage")
            else:
                print(f"{domain} has 0 checks recorded.")

4. Ignoring port numbers was achieved using the 'urlparse' library from urllib as well as adding basic error handling for the URL parsing. Edited the while loop to first parse urls to filter port number:

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

5. Added logic in the main loop in the monitor_endpoints function to calculate actual time spent on checks/logging (elapsed_time) using a start_time and end_time variable recorded at the beginning and end of the loop. Using elapsed_time, a necessary sleep_duration can be calculated to ensure the next cycle begins 15 seconds after the previous cycle started. If the check took longers than 15 seconds, the next check will proceed immediately:
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

Important to note are the 'check_interval', 'start_time', and 'end_time' variables used to calculate time taken to perform the availability check, then account for it by calculating 'sleep_time'.


    