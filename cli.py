import argparse
from support import SupportService

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='CLI tools for the MA Constitutional analysis suite')
    parser.add_argument('--suite', help="Which CLI suite to run", required=True)
    parser.add_argument('--method', help="Which CLI method to run", required=True)
    parser.add_argument('--supplement', help="Any supporting data", required=False)

    args = parser.parse_args()

    if args.suite == "support":
        support_service = SupportService()

        if args.method == "create-assistant":
            support_service.create_assistant()

        elif args.method == "create-vector":
            support_service.create_vector_store()

        elif args.method == "join-vector-assistant":
            support_service.join_vector_assistant()

        elif args.method == "compare-bill":
            bill_url = args.supplement
            response = support_service.compare_bill(bill_url)
            print(response)