import aws_cdk as cdk

from infra.stacks.my_stack import MyStack


def main() -> None:
    """Entry point for the CDK app."""
    app = cdk.App()

    # instantiate stack
    MyStack(app, "MyStack")

    # synth the Cloud Assembly
    app.synth()


if __name__ == "__main__":
    main()
