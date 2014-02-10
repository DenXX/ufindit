
general_hint = """You can press Ctrl+F (or Cmd+F or MacOS) to search for text on a webpage"""

missing_hint = """If search results missed some query terms, try to:
               <ul>
                <li style="padding-bottom:5px">remove unnecessary terms from the query, leave only keywords about the main topic of the query</li>
                <li style="padding-bottom:5px">add related terms (likely to appear on the answer page)</li>
                <li style="padding-bottom:5px">extend query with synonyms for missing terms, e.g. you can use OR query operator to separate synonyms</li>
               </ul>"""

misinterpreted_hint = """If search results misinterpreted some query terms, try to:
                <ul>
                    <li style="padding-bottom:5px">add related terms and synonyms (e.g. using OR operator to separate synonyms)</li>
                    <li style="padding-bottom:5px">filter documents containing irrelevant terms by a term you don't want to see in the results with minus operator (e.g. query <em>Hubble -telescope</em>)</li>
                    </ul>
                """

missing_relations_hint = """If search results missed relations between query terms, try to:
                        <ul>
                            <li style="padding-bottom:5px">remove unnecessary terms from the query, leave only keywords about the main topic of the query</li>
                            <li style="padding-bottom:5px">search for documents containing exact phrase using &quot; operator (e.g. <em>"Hubble telescope"</em> will search
                                for documents containing the phrase Hubble telescope)</li>
                            <li style="padding-bottom:5px">search for documents containing some terms near each other using <em>near:</em> operator (e.g. query <em>Hubble near:5 telescope</em> will rank
                                documents containing the terms Hubble and telescope within 5 words of each other higher)</li>
                        </ul>
                      """

def get_search_hints_old(serp, all = False):
    qu_judgements = serp.queryurljudgement_set.all()
    if len(qu_judgements) == 0 and not all:
        return None

    missing = 0
    misinterpreted = 0
    missing_relations = 0
    total = 0.1 # So just we don't have 0

    missing_terms = set([])
    misinterpreted_terms = set([])
    missing_relations_terms = set([])

    for judgement in qu_judgements:
        if judgement.missing_terms:
            missing += 1
            total += 1
            missing_terms.update(judgement.missing_terms.split(','))
        if judgement.misinterpreted_terms:
            misinterpreted += 1
            total += 1
            misinterpreted_terms.update(judgement.misinterpreted_terms.split(','))
        if judgement.missing_relations:
            missing_relations += 1
            total += 1
            missing_relations_terms.update(judgement.missing_relations.split(','))

    hints = [general_hint, ]
    if all or 1.0 * missing / total > 0.2:
        hints.append(missing_hint)
    if all or 1.0 * misinterpreted / total > 0.2:
        hints.append(misinterpreted_hint)
    if all or 1.0 * missing_relations / total > 0.2:
        hints.append(missing_relations_hint)

    return hints

task_hints = {
    2: """
            <ol>
                <li style="padding-bottom:5px">Find the names of the gods from the Archaic triad</li>
                <li style="padding-bottom:5px">For each of the gods find a Greek counterpart</li>
            </ol>
       """,
    16: """
            <ol>
                <li style="padding-bottom:5px">Find what is senescence</li>
                <li style="padding-bottom:5px">Find who do not undergo senescence</li>
                <li style="padding-bottom:5px">Find animals who can regenerate body and choose the one that satisfy both conditions</li>
            </ol>
          """,
    17: """
            <ol>
                <li style="padding-bottom:5px">Find the name of the battle mentioned in the questions</li>
                <li style="padding-bottom:5px">Search for coded communications language used in this battle</li>
            </ol>
          """,
    24: """
            <ol>
                <li style="padding-bottom:5px">Find what is the "waterless place" mentioned in the question?</li>
                <li style="padding-bottom:5px">Search for important eggs discovery in this "waterless place"</li>
            </ol>
          """,
    20: """
            <ol>
                <li style="padding-bottom:5px">Find what is Georges Lemaitre theory</li>
                <li style="padding-bottom:5px">Search for radiation that is an evidence of this theory</li>
            </ol>
          """,
    25: """
            <ol>
                <li style="padding-bottom:5px">Find who was the second wife of King Henry VIII</li>
                <li style="padding-bottom:5px">Find ghost stories about this person</li>
            </ol>
          """
}

general_hint = """
<ol>
    <li style="padding-bottom:5px">Split question into 2 or more logical parts</li>
    <li style="padding-bottom:5px">Find answers to the parts of the question</li>  
    <li style="padding-bottom:5px">Use answers to the parts of the question to find answer to the full question</li>
</ol>
For example:
<div class="well">
Question: The second wife of King Henry VIII is said to haunt the grounds where she was executed. What does she supposedly have tucked under her arm?
<br /><br />
<ul>
    <li>Search [second wife King Henry VIII] to find Anne Boleyn.</li>
    <li>Search [Anne Boleyn under arm] to find that her ghost is in the London Tower where she is said to carry her head tucked underneath her arm.</li>
</ul>
</div>
"""

def get_search_hints(task, serp, all = False):
    if not all:
        return task_hints[task.id] if task.id in task_hints else ''
    else:
        return general_hint