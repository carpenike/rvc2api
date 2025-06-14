#!/bin/bash

# Notification System Integration Test Runner
#
# This script runs comprehensive integration tests for the CoachIQ notification system.
# It supports running tests with both mocked services (default) and real external services.
#
# Usage:
#   ./scripts/run_notification_integration_tests.sh [OPTIONS]
#
# Options:
#   --mock-only       Run only tests with mocked services (default)
#   --real-smtp       Run tests with real SMTP server (requires configuration)
#   --real-pushover   Run tests with real Pushover API (requires configuration)
#   --real-all        Run tests with all real services (requires configuration)
#   --performance     Run performance and load tests
#   --verbose         Enable verbose output
#   --help            Show this help message

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default configuration
RUN_MOCK_TESTS=true
RUN_REAL_SMTP=false
RUN_REAL_PUSHOVER=false
RUN_PERFORMANCE=false
VERBOSE=false

# Test file paths
INTEGRATION_TEST_FILE="tests/integration/test_notification_integration.py"
REAL_SERVICE_TEST_FILE="tests/integration/test_notification_real_services.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
Notification System Integration Test Runner

This script runs comprehensive integration tests for the CoachIQ notification system.

USAGE:
    ./scripts/run_notification_integration_tests.sh [OPTIONS]

OPTIONS:
    --mock-only       Run only tests with mocked services (default)
    --real-smtp       Run tests with real SMTP server
    --real-pushover   Run tests with real Pushover API
    --real-all        Run tests with all real services
    --performance     Include performance and load tests
    --verbose         Enable verbose output
    --help            Show this help message

ENVIRONMENT VARIABLES FOR REAL SERVICE TESTING:

SMTP Configuration:
    COACHIQ_TEST_SMTP_ENABLED=true     # Enable real SMTP testing
    COACHIQ_TEST_SMTP_HOST             # SMTP server hostname
    COACHIQ_TEST_SMTP_PORT             # SMTP server port (default: 587)
    COACHIQ_TEST_SMTP_USERNAME         # SMTP username
    COACHIQ_TEST_SMTP_PASSWORD         # SMTP password
    COACHIQ_TEST_SMTP_TLS=true         # Use TLS (default: true)
    COACHIQ_TEST_FROM_EMAIL            # From email address
    COACHIQ_TEST_EMAIL                 # Target email for testing

Pushover Configuration:
    COACHIQ_TEST_PUSHOVER_ENABLED=true # Enable Pushover testing
    COACHIQ_TEST_PUSHOVER_TOKEN        # Pushover app token
    COACHIQ_TEST_PUSHOVER_USER         # Pushover user key

EXAMPLES:

    # Run only mock tests (safe, no external dependencies)
    ./scripts/run_notification_integration_tests.sh --mock-only

    # Run with real Gmail SMTP
    COACHIQ_TEST_SMTP_ENABLED=true \\
    COACHIQ_TEST_SMTP_HOST=smtp.gmail.com \\
    COACHIQ_TEST_SMTP_USERNAME=your@gmail.com \\
    COACHIQ_TEST_SMTP_PASSWORD=your-app-password \\
    COACHIQ_TEST_EMAIL=target@email.com \\
    ./scripts/run_notification_integration_tests.sh --real-smtp

    # Run performance tests
    ./scripts/run_notification_integration_tests.sh --performance

    # Run all tests with real services
    ./scripts/run_notification_integration_tests.sh --real-all --verbose

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --mock-only)
            RUN_MOCK_TESTS=true
            RUN_REAL_SMTP=false
            RUN_REAL_PUSHOVER=false
            shift
            ;;
        --real-smtp)
            RUN_REAL_SMTP=true
            RUN_MOCK_TESTS=false
            shift
            ;;
        --real-pushover)
            RUN_REAL_PUSHOVER=true
            RUN_MOCK_TESTS=false
            shift
            ;;
        --real-all)
            RUN_REAL_SMTP=true
            RUN_REAL_PUSHOVER=true
            RUN_MOCK_TESTS=false
            shift
            ;;
        --performance)
            RUN_PERFORMANCE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Change to project root
cd "$PROJECT_ROOT"

# Check if we're in a Poetry environment
check_poetry() {
    if ! command -v poetry &> /dev/null; then
        log_error "Poetry not found. Please install Poetry to run tests."
        exit 1
    fi

    if ! poetry env info &> /dev/null; then
        log_error "Not in a Poetry environment. Please run 'poetry shell' or 'poetry install' first."
        exit 1
    fi
}

# Check test environment
check_test_environment() {
    log_info "Checking test environment..."

    # Check required test files exist
    if [[ ! -f "$INTEGRATION_TEST_FILE" ]]; then
        log_error "Integration test file not found: $INTEGRATION_TEST_FILE"
        exit 1
    fi

    if [[ ! -f "$REAL_SERVICE_TEST_FILE" ]]; then
        log_error "Real service test file not found: $REAL_SERVICE_TEST_FILE"
        exit 1
    fi

    # Validate real service configuration if needed
    if [[ "$RUN_REAL_SMTP" == "true" ]]; then
        if [[ -z "$COACHIQ_TEST_SMTP_HOST" || -z "$COACHIQ_TEST_EMAIL" ]]; then
            log_error "Real SMTP testing enabled but missing required environment variables."
            log_error "Required: COACHIQ_TEST_SMTP_HOST, COACHIQ_TEST_EMAIL"
            exit 1
        fi
        export COACHIQ_TEST_SMTP_ENABLED=true
        log_info "Real SMTP testing enabled for: $COACHIQ_TEST_SMTP_HOST"
    fi

    if [[ "$RUN_REAL_PUSHOVER" == "true" ]]; then
        if [[ -z "$COACHIQ_TEST_PUSHOVER_TOKEN" || -z "$COACHIQ_TEST_PUSHOVER_USER" ]]; then
            log_error "Real Pushover testing enabled but missing required environment variables."
            log_error "Required: COACHIQ_TEST_PUSHOVER_TOKEN, COACHIQ_TEST_PUSHOVER_USER"
            exit 1
        fi
        export COACHIQ_TEST_PUSHOVER_ENABLED=true
        log_info "Real Pushover testing enabled"
    fi
}

# Set pytest options based on configuration
set_pytest_options() {
    PYTEST_OPTS=""

    if [[ "$VERBOSE" == "true" ]]; then
        PYTEST_OPTS="$PYTEST_OPTS -v -s"
    else
        PYTEST_OPTS="$PYTEST_OPTS -q"
    fi

    # Add coverage if not running real services
    if [[ "$RUN_REAL_SMTP" == "false" && "$RUN_REAL_PUSHOVER" == "false" ]]; then
        PYTEST_OPTS="$PYTEST_OPTS --cov=backend.services --cov-report=term-missing"
    fi
}

# Run mock-only tests
run_mock_tests() {
    log_info "Running integration tests with mocked services..."

    if poetry run pytest $PYTEST_OPTS "$INTEGRATION_TEST_FILE" -k "not test_real_"; then
        log_success "Mock service integration tests passed"
    else
        log_error "Mock service integration tests failed"
        return 1
    fi
}

# Run real SMTP tests
run_real_smtp_tests() {
    log_info "Running integration tests with real SMTP service..."

    if poetry run pytest $PYTEST_OPTS "$REAL_SERVICE_TEST_FILE::TestRealEmailDelivery"; then
        log_success "Real SMTP integration tests passed"
    else
        log_error "Real SMTP integration tests failed"
        return 1
    fi
}

# Run real Pushover tests
run_real_pushover_tests() {
    log_info "Running integration tests with real Pushover service..."

    if poetry run pytest $PYTEST_OPTS "$REAL_SERVICE_TEST_FILE::TestRealPushoverDelivery"; then
        log_success "Real Pushover integration tests passed"
    else
        log_error "Real Pushover integration tests failed"
        return 1
    fi
}

# Run performance tests
run_performance_tests() {
    log_info "Running performance and load tests..."

    if poetry run pytest $PYTEST_OPTS "$INTEGRATION_TEST_FILE::TestNotificationSystemPerformance"; then
        log_success "Performance tests passed"
    else
        log_error "Performance tests failed"
        return 1
    fi
}

# Run combined real service tests
run_combined_real_tests() {
    log_info "Running combined real service tests..."

    if poetry run pytest $PYTEST_OPTS "$REAL_SERVICE_TEST_FILE::TestRealServiceCombination"; then
        log_success "Combined real service tests passed"
    else
        log_error "Combined real service tests failed"
        return 1
    fi
}

# Main execution
main() {
    log_info "Starting notification system integration tests..."

    # Pre-flight checks
    check_poetry
    check_test_environment
    set_pytest_options

    # Track test results
    FAILED_TESTS=()

    # Run mock tests if requested
    if [[ "$RUN_MOCK_TESTS" == "true" ]]; then
        if ! run_mock_tests; then
            FAILED_TESTS+=("mock_tests")
        fi
    fi

    # Run real service tests if requested
    if [[ "$RUN_REAL_SMTP" == "true" ]]; then
        if ! run_real_smtp_tests; then
            FAILED_TESTS+=("real_smtp")
        fi
    fi

    if [[ "$RUN_REAL_PUSHOVER" == "true" ]]; then
        if ! run_real_pushover_tests; then
            FAILED_TESTS+=("real_pushover")
        fi
    fi

    # Run combined tests if both real services enabled
    if [[ "$RUN_REAL_SMTP" == "true" && "$RUN_REAL_PUSHOVER" == "true" ]]; then
        if ! run_combined_real_tests; then
            FAILED_TESTS+=("combined_real")
        fi
    fi

    # Run performance tests if requested
    if [[ "$RUN_PERFORMANCE" == "true" ]]; then
        if ! run_performance_tests; then
            FAILED_TESTS+=("performance")
        fi
    fi

    # Report final results
    echo
    echo "=============================================="
    echo "Integration Test Results"
    echo "=============================================="

    if [[ ${#FAILED_TESTS[@]} -eq 0 ]]; then
        log_success "All integration tests passed! ✅"
        exit 0
    else
        log_error "Some integration tests failed: ${FAILED_TESTS[*]}"

        echo
        echo "Failed test categories:"
        for failed_test in "${FAILED_TESTS[@]}"; do
            echo "  - $failed_test"
        done

        echo
        echo "Troubleshooting tips:"
        echo "  - Check environment variable configuration"
        echo "  - Verify network connectivity to external services"
        echo "  - Review test logs for specific error details"
        echo "  - Try running with --verbose for more information"

        exit 1
    fi
}

# Run main function
main "$@"
