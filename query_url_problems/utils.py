
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
    16: """
            <ol>
                <li style="padding-bottom:5px">Find what is senescence</li>
                <li style="padding-bottom:5px">Find who do not undergo senescence</li>
                <li style="padding-bottom:5px">Find animals who can regenerate body and choose the one that satisfy both conditions</li>
            </ol>
            BTW, you can press Ctrl+F (or Cmd+F or MacOS) to search for text on a webpage
          """,
    24: """
            <ol>
                <li style="padding-bottom:5px">Find what is the "waterless place"?</li>
                <li style="padding-bottom:5px">Search for important eggs discovery in this "waterless place"</li>
            </ol>
            BTW, you can press Ctrl+F (or Cmd+F or MacOS) to search for text on a webpage
          """,
    20: """
            <ol>
                <li style="padding-bottom:5px">Find what is Georges Lemaitre theory</li>
                <li style="padding-bottom:5px">Search for radiation that is an evidence of this theory</li>
            </ol>
            BTW, you can press Ctrl+F (or Cmd+F or MacOS) to search for text on a webpage
          """,
    25: """
            <ol>
                <li style="padding-bottom:5px">Find who was the second wife of King Henry VIII</li>
                <li style="padding-bottom:5px">Find ghost stories about this person</li>
            </ol>
            BTW, you can press Ctrl+F (or Cmd+F or MacOS) to search for text on a webpage
          """
}

def get_search_hints(task, serp, all = False):
    return task_hints[task.id]