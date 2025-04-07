import aws_cdk as cdk
from infra.stacks.my_stack import MyStack

def main() -> None:
    """Main entry point for the CDK app."""
    app = cdk.App()

    # Instantiate the stack
    MyStack(app, "MyStack")

    # Synthesize the Cloud Assembly
    app.synth()

if __name__ == "__main__":
    main()

