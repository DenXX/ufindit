
general_hint = "You can rephrase the query, try adding terms that are likely to appear on the webpage containing the answer"

missing_hint = """Search results might've missed some search terms you provided. You can try:
               <ul>
                <li style="padding-bottom:5px">Remove terms that are not required to be in a document containing the answer</li>
                <li style="padding-bottom:5px">Add other terms related to the topic of interest (add terms are likely to appear in a page containing the answer)</li>
                <li style="padding-bottom:5px">Extend query with synonyms for missing terms, e.g. you can use OR query operator 
                (e.g. query <em>Hubble achievements OR accomplishments</em> will search for documents that contain term achievements or accomplishments or both)</li>
               </ul>"""

misinterpreted_hint = """Search results might've misinterpreted some search terms you provided. You can try:
                <ul>
                    <li style="padding-bottom:5px">Add other terms related to the topic of interest (think which terms are likely to appear in a page containing the answer)</li>
                    <li style="padding-bottom:5px">Remove documents containing irrelevant terms by adding - before the term (e.g. query <em>Hubble -telescope</em> will search
                    for documents that contain the term Hubble but doesn't contain term telescope)</li>
                    <li style="padding-bottom:5px">Extend query with synonyms for missing terms, e.g. you can use OR query operator 
                    (e.g. query <em>Hubble achievements OR accomplishments</em> will search for documents that contain term achievements or accomplishments or both)</li>
                </ul>
                """

missing_relations_hint = """Search results might've missed relations between some search terms you provided. You can try:
                        <ul>
                            <li style="padding-bottom:5px">search for documents containing exact phrase using &quot; operator (e.g. query <em>"Hubble telescope"</em> will search
                                for documents containing the phrase Hubble telescope)</li>
                            <li style="padding-bottom:5px">search for documents containing some terms near each other using near: operator (e.g. query <em>Hubble near:5 telescope</em> will rank
                                documents containing the terms Hubble and telescope within 5 words of each other higher)</li>
                        </ul>
                      """

def get_search_hints(serp, all = False):
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