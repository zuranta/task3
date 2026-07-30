import { Answer } from "../services/queries";
import { CitationList } from "./CitationList";

export function AnswerCard({ answer }: { answer: Answer }) {
  if (answer.status === "no_answer_found") {
    return <p>No answer was found in your documents.</p>;
  }

  return (
    <div aria-label="Answer">
      <p>{answer.answer_text}</p>
      <CitationList citations={answer.citations} />
    </div>
  );
}
