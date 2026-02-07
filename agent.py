import sys
import argparse
import uuid
import os
from dotenv import load_dotenv

load_dotenv(override=True)

from state import StateManager
from storage_utils import load_json, save_json, update_json_list
from slack_reader import fetch_slack_threads, normalize_thread
from llm_pipeline.classify_points import classify_conversation, create_artifact_from_classification
from src.adapters.repo_json import (
    JsonArtifactRepository,
    JsonOpenQuestionRepository,
    JsonProposedUpdateRepository,
)
from src.use_cases.transform_artifacts import TransformArtifactsUseCase
from oq_utils import create_pu_from_oq

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

        # Command: oq_transform
        oq_trans_parser = subparsers.add_parser("oq_transform", help="Transform an OQ into a PU")
        oq_trans_parser.add_argument("oq_id", help="OQ ID")

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
        
        threads = fetch_slack_threads(channel_id)
        if not threads:
            print("No new threads found.")
            return

        # Traceability: Save raw threads
        save_json("slack_threads.json", {"threads": threads})
        
        self.state_manager.start_run()
        
        # Load existing artifacts to check for duplicates
        existing_artifacts = load_json("artifacts.json").get("artifacts", [])
        existing_conv_ids = {art["conversation_id"] for art in existing_artifacts}
        
        conversations = []
        artifacts_created = 0
        
        for thread in threads:
            ts = thread["ts"]
            conv_text = normalize_thread(thread)
            
            # Traceability: Collect normalized conversations
            conversations.append({"ts": ts, "text": conv_text})
            
            # Duplicate check
            if ts in existing_conv_ids:
                print(f"Skipping thread {ts} (already exists in artifacts).")
                continue

            classification = classify_conversation(conv_text)
            
            if classification and classification.get("type") != "IRRELEVANT":
                create_artifact_from_classification(ts, classification)
                artifacts_created += 1

        # Traceability: Save normalized conversations
        save_json("conversations.json", {"conversations": conversations})

        if artifacts_created > 0:
            self.state_manager.set_state("ARTIFACTS PROCESSING")
            print(f"Successfully created {artifacts_created} new artifacts.")
            print("State changed to: ARTIFACTS PROCESSING")
        else:
            print("No new relevant artifacts found in the ingested threads.")
            self.state_manager.end_run()

    def cmd_change_status(self, args):
        print(f"Changing status of {args.artifact_id} to {args.status}...")
        data = load_json("artifacts.json")
        for art in data.get("artifacts", []):
            if art["id"] == args.artifact_id:
                art["status"] = args.status
                break
        save_json("artifacts.json", data)
        print("Status updated.")

    def cmd_artifact_transform(self, args):
        print("Transforming artifacts...")
        artifact_repo = JsonArtifactRepository()
        oq_repo = JsonOpenQuestionRepository()
        pu_repo = JsonProposedUpdateRepository()
        use_case = TransformArtifactsUseCase(artifact_repo, oq_repo, pu_repo)

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
        print(f"Transforming OQ {args.oq_id} to PU...")
        decision = input("Enter the decision for this OQ: ")
        rationale = input("Enter the rationale (optional): ")
        
        pu = create_pu_from_oq(args.oq_id, decision, rationale)
        if pu:
            print(f"Created Proposed Update: {pu['id']}")
            # Check if more OQs are OPEN
            oq_data = load_json("open_questions.json")
            open_count = sum(1 for oq in oq_data.get("questions", []) if oq["status"] == "OPEN")
            if open_count == 0:
                self.state_manager.set_state("PU PROCESSING")
                print("All OQs processed. State changed to: PU PROCESSING")

    def cmd_approve_pu(self, args):
        print(f"Approving PU {args.pu_id}...")
        pu_data = load_json("proposed_updates.json")
        target_pu = None
        for pu in pu_data.get("updates", []):
            if pu["id"] == args.pu_id:
                pu["status"] = "APPROVED"
                target_pu = pu
                break
        
        if target_pu:
            save_json("proposed_updates.json", pu_data)
            # Create SU
            su = {
                "id": f"su_{uuid.uuid4().hex[:8]}",
                "pu_id": target_pu["id"],
                "content": target_pu["rephrasing"],
                "decision": target_pu["decision"],
                "status": "ACTIVE"
            }
            update_json_list("specs_updates.json", "updates", su)
            print(f"Spec Update {su['id']} created.")
            
            # Check if more PUs are DRAFT
            draft_count = sum(1 for pu in pu_data.get("updates", []) if pu["status"] == "DRAFT")
            if draft_count == 0:
                self.state_manager.set_state("FINALIZE")
                print("All PUs processed. State changed to: FINALIZE")

    def cmd_oq_modify(self, args):
        print(f"Modifying OQ {args.oq_id} (Not yet fully implemented)")

    def cmd_init_sync(self, args):
        channel_id = args.channel or os.getenv("SLACK_CHANNEL_ID", "general")
        import time
        current_ts = str(time.time())
        
        sources_state = load_json("sources_state.json")
        if "slack" not in sources_state:
            sources_state["slack"] = {}
        
        sources_state["slack"][channel_id] = {"last_ts": current_ts}
        save_json("sources_state.json", sources_state)
        
        print(f"Sync initialized for channel {channel_id} at timestamp {current_ts}.")
        print("Future 'ingest' commands will only fetch messages from this point forward.")

    def cmd_art_list(self, args):
        data = load_json("artifacts.json")
        artifacts = data.get("artifacts", [])
        if not artifacts:
            print("No artifacts found.")
            return
        print(f"{'ID':<15} {'Status':<15} {'Rephrasing'}")
        print("-" * 70)
        for art in artifacts:
            rephrasing = art.get('rephrasing', 'N/A')
            if len(rephrasing) > 60:
                rephrasing = rephrasing[:57] + "..."
            print(f"{art['id']:<15} {art['status']:<15} {rephrasing}")

    def cmd_oq_list(self, args):
        data = load_json("open_questions.json")
        questions = data.get("questions", [])
        if not questions:
            print("No open questions found.")
            return
        print(f"{'ID':<25} {'Status':<15} {'Question'}")
        print("-" * 80)
        for oq in questions:
            question = oq.get('question', 'N/A')
            if len(question) > 60:
                question = question[:57] + "..."
            print(f"{oq['id']:<25} {oq['status']:<15} {question}")

    def cmd_pu_list(self, args):
        data = load_json("proposed_updates.json")
        updates = data.get("updates", [])
        if not updates:
            print("No proposed updates found.")
            return
        print(f"{'ID':<25} {'Status':<15} {'Rephrasing'}")
        print("-" * 80)
        for pu in updates:
            rephrasing = pu.get('rephrasing', 'N/A')
            if len(rephrasing) > 60:
                rephrasing = rephrasing[:57] + "..."
            print(f"{pu['id']:<25} {pu['status']:<15} {rephrasing}")

if __name__ == "__main__":
    agent = SpecsUpdatesAgent()
    agent.run()
