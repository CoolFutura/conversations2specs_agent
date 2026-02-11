import sys
import argparse
import os
import time
from dotenv import load_dotenv

load_dotenv(override=True)

from state import StateManager
from src.cli.wiring import (
    build_ingest_threads_use_case,
    build_fetch_threads_use_case,
    build_trace_ingest_use_case,
    build_transform_artifacts_use_case,
    build_transform_oq_use_case,
    build_add_decision_use_case,
    build_modify_oq_use_case,
    build_approve_pu_use_case,
    build_change_artifact_status_use_case,
    build_list_artifacts_use_case,
    build_list_open_questions_use_case,
    build_list_proposed_updates_use_case,
    build_init_sync_use_case,
)

class SpecsUpdatesAgent:
    def __init__(self):
        self.state_manager = StateManager()

    def run(self):
        parser = argparse.ArgumentParser(description="Specs Updates Generator CLI")
        subparsers = parser.add_subparsers(dest="command")

        # Command: ingest
        ingest_parser = subparsers.add_parser("ingest", help="Ingest Slack threads and classify artifacts")
        ingest_parser.add_argument("--channel", default=os.getenv("SLACK_CHANNEL_ID", "general"), help="Slack channel ID to ingest from (defaults to SLACK_CHANNEL_ID in .env or 'general')")
        
        # Command: change_status
        status_parser = subparsers.add_parser("change_status", help="Change status of an artifact")
        status_parser.add_argument("artifact_id", help="Artifact ID")
        status_parser.add_argument("status", choices=["OQ", "PU", "IRRELEVANT"], help="New status")

        # Command: artifact_transform
        subparsers.add_parser("artifact_transform", help="Transform artifacts into OQ or PU")

        # Command: oq_modify
        oq_mod_parser = subparsers.add_parser("oq_modify", help="Modify an Open Question")
        oq_mod_parser.add_argument("oq_id", help="OQ ID")

        # Command: oq_decide
        oq_decide_parser = subparsers.add_parser("oq_decide", help="Add a decision to an Open Question")
        oq_decide_parser.add_argument("oq_id", help="OQ ID")

        # Command: oq_transform
        subparsers.add_parser("oq_transform", help="Transform decided OQs into PUs")

        # Command: approve_pu
        pu_app_parser = subparsers.add_parser("approve_pu", help="Approve a Proposed Update")
        pu_app_parser.add_argument("pu_id", help="PU ID")

        # Command: init_sync
        init_parser = subparsers.add_parser("init_sync", help="Initialize the sync timestamp to current time to skip history")
        init_parser.add_argument("--channel", help="Specific channel ID to initialize (optional, uses .env or --channel)")

        # Command: art_list
        subparsers.add_parser("art_list", help="List all artifacts")

        # Command: oq_list
        subparsers.add_parser("oq_list", help="List all open questions")

        # Command: pu_list
        subparsers.add_parser("pu_list", help="List all proposed updates")

        args = parser.parse_args()

        if not args.command:
            parser.print_help()
            return

        self.handle_command(args)

    def handle_command(self, args):
        current_state = self.state_manager.get_current_state()
        print(f"Current State: {current_state}")
        
        # Dispatch command to method
        method_name = f"cmd_{args.command}"
        if hasattr(self, method_name):
            getattr(self, method_name)(args)
        else:
            print(f"Command {args.command} not implemented yet.")

    def cmd_ingest(self, args):
        channel_id = args.channel
        print(f"Ingesting Slack threads from {channel_id}...")
        
        fetch_use_case = build_fetch_threads_use_case()
        threads = fetch_use_case.execute(channel_id).threads
        if not threads:
            print("No new threads found.")
            return

        # Traceability: Save raw threads + normalized conversations
        trace_use_case = build_trace_ingest_use_case()
        
        self.state_manager.start_run()

        use_case = build_ingest_threads_use_case()
        result = use_case.execute(threads)
        conversations = result.conversations
        artifacts_created = result.artifacts_created

        trace_use_case.execute(threads, conversations)

        if artifacts_created > 0:
            self.state_manager.set_state("ARTIFACTS PROCESSING")
            print(f"Successfully created {artifacts_created} new artifacts.")
            print("State changed to: ARTIFACTS PROCESSING")
        else:
            print("No new relevant artifacts found in the ingested threads.")
            self.state_manager.end_run()

    def cmd_change_status(self, args):
        print(f"Changing status of {args.artifact_id} to {args.status}...")
        use_case = build_change_artifact_status_use_case()
        result = use_case.execute(args.artifact_id, args.status)

        if not result.updated:
            print(f"Artifact {args.artifact_id} not found.")
            return

        print("Status updated.")

    def cmd_artifact_transform(self, args):
        print("Transforming artifacts...")
        use_case = build_transform_artifacts_use_case()

        oq_count, pu_count = use_case.execute()
        print(f"Created {oq_count} Open Questions and {pu_count} Proposed Updates.")
        
        if oq_count > 0:
            self.state_manager.set_state("OQ PROCESSING")
        elif pu_count > 0:
            self.state_manager.set_state("PU PROCESSING")
        else:
            self.state_manager.set_state("IDLE")
            self.state_manager.end_run()
        
        print(f"New state: {self.state_manager.get_current_state()}")

    def cmd_oq_transform(self, args):
        print("Transforming decided OQs to PUs...")
        use_case = build_transform_oq_use_case()
        result = use_case.execute()

        print(f"Created {result.transformed_count} Proposed Updates.")
        if result.open_questions_remaining == 0 and result.transformed_count > 0:
            self.state_manager.set_state("PU PROCESSING")
            print("All OQs processed. State changed to: PU PROCESSING")

    def cmd_oq_decide(self, args):
        print(f"Adding decision to OQ {args.oq_id}...")
        decision = input("Enter the decision for this OQ: ")
        rationale = input("Enter the rationale: ")

        use_case = build_add_decision_use_case()
        result = use_case.execute(args.oq_id, decision, rationale)

        if not result.updated:
            print(f"OQ {args.oq_id} not found.")
            return

        print(f"Decision saved for OQ {args.oq_id}.")

    def cmd_approve_pu(self, args):
        print(f"Approving PU {args.pu_id}...")
        use_case = build_approve_pu_use_case()
        result = use_case.execute(args.pu_id)

        if not result.spec_update:
            print(f"PU {args.pu_id} not found.")
            return

        print(f"Spec Update {result.spec_update.id} created.")
        if result.remaining_drafts == 0:
            self.state_manager.set_state("FINALIZE")
            print("All PUs processed. State changed to: FINALIZE")

    def cmd_oq_modify(self, args):
        oq_repo = JsonOpenQuestionRepository()
        oq = oq_repo.get_by_id(args.oq_id)
        if not oq:
            print(f"OQ {args.oq_id} not found.")
            return

        print(f"Modifying OQ {args.oq_id}...")

        def ask_yes_no(prompt):
            answer = input(f"{prompt} (y/n): ").strip().lower()
            return answer in {"y", "yes"}

        updates = {}
        print(f"Current question: {oq.question}")
        if ask_yes_no("Do you want to modify the question"):
            updates["question"] = input("New question: ")
        print(f"Current context: {oq.context}")
        if ask_yes_no("Do you want to modify the context"):
            updates["context"] = input("New context: ")
        print(f"Current decision: {oq.decision or ''}")
        if ask_yes_no("Do you want to modify the decision"):
            updates["decision"] = input("New decision: ")
        print(f"Current decision rationale: {oq.decision_rationale or ''}")
        if ask_yes_no("Do you want to modify the decision rationale"):
            updates["decision_rationale"] = input("New decision rationale: ")

        if not updates:
            print("No changes made.")
            return

        use_case = build_modify_oq_use_case()
        result = use_case.execute(args.oq_id, **updates)

        if not result.updated:
            print(f"OQ {args.oq_id} not found.")
            return

        print(f"OQ {args.oq_id} updated.")

    def cmd_init_sync(self, args):
        channel_id = args.channel or os.getenv("SLACK_CHANNEL_ID", "general")
        current_ts = str(time.time())

        use_case = build_init_sync_use_case()
        use_case.execute(channel_id, current_ts)
        
        print(f"Sync initialized for channel {channel_id} at timestamp {current_ts}.")
        print("Future 'ingest' commands will only fetch messages from this point forward.")

    def cmd_art_list(self, args):
        use_case = build_list_artifacts_use_case()
        artifacts = use_case.execute()
        if not artifacts:
            print("No artifacts found.")
            return
        print(f"{'ID':<15} {'Status':<15} {'Rephrasing'}")
        print("-" * 70)
        for art in artifacts:
            rephrasing = art.rephrasing or "N/A"
            if len(rephrasing) > 60:
                rephrasing = rephrasing[:57] + "..."
            print(f"{art.id:<15} {art.status:<15} {rephrasing}")

    def cmd_oq_list(self, args):
        use_case = build_list_open_questions_use_case()
        questions = use_case.execute()
        if not questions:
            print("No open questions found.")
            return
        print(f"{'ID':<25} {'Status':<15} {'Decided':<10} {'Question'}")
        print("-" * 95)
        for oq in questions:
            question = oq.question or "N/A"
            if len(question) > 60:
                question = question[:57] + "..."
            decision = oq.decision
            rationale = oq.decision_rationale
            decided = "YES" if decision and rationale and str(decision).strip() and str(rationale).strip() else "NO"
            print(f"{oq.id:<25} {oq.status:<15} {decided:<10} {question}")

    def cmd_pu_list(self, args):
        use_case = build_list_proposed_updates_use_case()
        updates = use_case.execute()
        if not updates:
            print("No proposed updates found.")
            return
        print(f"{'ID':<25} {'Status':<15} {'Rephrasing'}")
        print("-" * 80)
        for pu in updates:
            rephrasing = pu.rephrasing or "N/A"
            if len(rephrasing) > 60:
                rephrasing = rephrasing[:57] + "..."
            print(f"{pu.id:<25} {pu.status:<15} {rephrasing}")

if __name__ == "__main__":
    agent = SpecsUpdatesAgent()
    agent.run()
